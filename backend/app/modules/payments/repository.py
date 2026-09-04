import calendar
from datetime import date, datetime
from typing import List, Optional
from app.core.database import supabase

class PaymentsRepository:
    @staticmethod
    def listar_categorias() -> List[dict]:
        res = supabase.table("categories").select("*").execute()
        return res.data or []

    @staticmethod
    def criar_despesa_recorrente(user_id: str, payload: dict) -> dict:
        total_installments = payload.get("total_installments")
        category_id = payload.get("category_id")
        
        # Tratamento do ID da categoria para preservar/restaurar zeros à esquerda
        if category_id is not None and str(category_id).strip() != "":
            category_id = str(category_id).strip()
            if category_id.isdigit() and len(category_id) < 8:
                category_id = category_id.zfill(8)
        else:
            category_id = None

        expense_data = {
            "user_id": user_id,
            "name": payload["name"],
            "description": payload.get("description"),
            "category_id": category_id,
            "due_day": payload["due_day"],
            "amount": payload["current_amount"],
            "total_installments": total_installments,
            "active": True
        }
        res_exp = supabase.table("recurring_expenses").insert(expense_data).execute()
        expense = res_exp.data[0]

        hoje = date.today()
        ref_month = f"{hoje.year}-{hoje.month:02d}"
        
        PaymentsRepository.garantir_faturas_do_mes(user_id, ref_month)
        return expense

    @staticmethod
    def garantir_faturas_do_mes(user_id: str, reference_month: str):
        """Varre os contratos ativos e gera a fatura mensal caso ainda não exista no mês selecionado."""
        res_expenses = supabase.table("recurring_expenses") \
            .select("*") \
            .eq("user_id", user_id) \
            .eq("active", True) \
            .execute()
        
        expenses = res_expenses.data or []
        if not expenses:
            return

        ano, mes = map(int, reference_month.split("-"))
        max_dias = calendar.monthrange(ano, mes)[1]

        for exp in expenses:
            res_ex = supabase.table("monthly_payments") \
                .select("id") \
                .eq("expense_id", exp["id"]) \
                .eq("reference_month", reference_month) \
                .execute()

            if not res_ex.data:
                due_day = min(exp["due_day"], max_dias)
                due_date_str = f"{ano:04d}-{mes:02d}-{due_day:02d}"

                installment_number = None
                if exp.get("total_installments"):
                    res_count = supabase.table("monthly_payments") \
                        .select("id", count="exact") \
                        .eq("expense_id", exp["id"]) \
                        .execute()
                    count = res_count.count or 0
                    start = exp.get("start_installment") or 1
                    installment_number = start + count

                valor_base = exp.get("amount") or exp.get("current_amount") or 0.0

                supabase.table("monthly_payments").insert({
                    "expense_id": exp["id"],
                    "reference_month": reference_month,
                    "due_date": due_date_str,
                    "amount": valor_base,
                    "status": "pending",
                    "installment_number": installment_number
                }).execute()

    @staticmethod
    def obter_pagamentos_mes(user_id: str, reference_month: str) -> List[dict]:
        PaymentsRepository.garantir_faturas_do_mes(user_id, reference_month)

        res = supabase.table("monthly_payments") \
            .select("*, recurring_expenses!inner(*, categories(*))") \
            .eq("recurring_expenses.user_id", user_id) \
            .eq("reference_month", reference_month) \
            .execute()
        return res.data or []

    @staticmethod
    def obter_pendencias_anteriores(user_id: str, reference_month: str) -> List[dict]:
        res = supabase.table("monthly_payments") \
            .select("*, recurring_expenses!inner(*, categories(*))") \
            .eq("recurring_expenses.user_id", user_id) \
            .eq("status", "pending") \
            .lt("reference_month", reference_month) \
            .order("due_date") \
            .execute()
        return res.data or []

    @staticmethod
    def obter_meses_disponiveis(user_id: str) -> List[str]:
        res = supabase.table("monthly_payments") \
            .select("reference_month, recurring_expenses!inner(user_id)") \
            .eq("recurring_expenses.user_id", user_id) \
            .execute()
        meses = {item["reference_month"] for item in (res.data or []) if item.get("reference_month")}
        hoje_mes = date.today().strftime("%Y-%m")
        meses.add(hoje_mes)
        return sorted(list(meses), reverse=True)

    @staticmethod
    def alternar_pagamento(monthly_id: str, user_id: str) -> dict:
        res = supabase.table("monthly_payments") \
            .select("status") \
            .eq("id", monthly_id) \
            .execute()
        
        if not res.data:
            raise ValueError("Pagamento não encontrado")

        status_atual = res.data[0]["status"]
        novo_status = "pending" if status_atual == "paid" else "paid"
        paid_at = datetime.utcnow().isoformat() if novo_status == "paid" else None

        res_up = supabase.table("monthly_payments") \
            .update({"status": novo_status, "paid_at": paid_at}) \
            .eq("id", monthly_id) \
            .execute()
        
        return res_up.data[0]

    @staticmethod
    def atualizar_valor_mensal(monthly_id: str, user_id: str, amount: float) -> dict:
        res_mp = supabase.table("monthly_payments") \
            .update({"amount": amount}) \
            .eq("id", monthly_id) \
            .execute()
        
        if not res_mp.data:
            raise ValueError("Registro de pagamento não encontrado.")
        
        monthly = res_mp.data[0]
        if monthly.get("expense_id"):
            supabase.table("recurring_expenses") \
                .update({"amount": amount}) \
                .eq("id", monthly["expense_id"]) \
                .execute()

        return monthly

    @staticmethod
    def excluir_despesa_recorrente(expense_id: str, user_id: str, mes_corte: str):
        supabase.table("recurring_expenses") \
            .update({"active": False}) \
            .eq("id", expense_id) \
            .eq("user_id", user_id) \
            .execute()

        supabase.table("monthly_payments") \
            .delete() \
            .eq("expense_id", expense_id) \
            .gte("reference_month", mes_corte) \
            .execute()

    @staticmethod
    def obter_historico_ano(user_id: str, ano: int) -> List[dict]:
        res = supabase.table("monthly_payments") \
            .select("reference_month, amount, status, recurring_expenses!inner(user_id)") \
            .eq("recurring_expenses.user_id", user_id) \
            .gte("reference_month", f"{ano}-01") \
            .lte("reference_month", f"{ano}-12") \
            .execute()

        dados = res.data or []
        meses_nomes = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        agrupado = {i + 1: {"previsto": 0.0, "realizado": 0.0} for i in range(12)}

        for item in dados:
            try:
                m = int(item["reference_month"].split("-")[1])
                amt = float(item["amount"] or 0)
                agrupado[m]["previsto"] += amt
                if item["status"] == "paid":
                    agrupado[m]["realizado"] += amt
            except Exception:
                pass

        return [
            {"mes": meses_nomes[m - 1], "previsto": round(agrupado[m]["previsto"], 2), "realizado": round(agrupado[m]["realizado"], 2)}
            for m in range(1, 13)
        ]