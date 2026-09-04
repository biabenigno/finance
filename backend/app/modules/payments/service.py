from datetime import date
from typing import List, Optional
from app.modules.payments.repository import PaymentsRepository
from app.modules.payments.schemas import (
    ExpenseCreate,
    MonthlyPaymentUpdate,
    PaymentItem,
    PaymentsKPIs,
    PaymentsDashboardResponse,
    HistoryResponse,
    CategorySimple
)

class PaymentsService:
    def __init__(self):
        self.repository = PaymentsRepository()

    def obter_categorias(self) -> List[CategorySimple]:
        cats = self.repository.listar_categorias()
        return [
            CategorySimple(
                id=str(c["id"]),
                name=c.get("description_translated") or c.get("description") or "Geral"
            )
            for c in cats
        ]

    def _formatar_pagamento(self, item: dict, is_stacked: bool = False) -> PaymentItem:
        exp = item.get("recurring_expenses") or {}
        if isinstance(exp, list) and len(exp) > 0:
            exp = exp[0]
        cat = exp.get("categories") or {}
        if isinstance(cat, list) and len(cat) > 0:
            cat = cat[0]

        today_str = date.today().strftime("%Y-%m-%d")
        due_date = item.get("due_date") or ""
        status = item.get("status") or "pending"
        is_overdue = bool(status == "pending" and due_date and due_date < today_str)

        return PaymentItem(
            id=str(item["id"]),
            expense_id=str(item.get("expense_id") or ""),
            name=exp.get("name") or "Conta sem nome",
            description=exp.get("description") or "",
            category_id=str(exp.get("category_id")) if exp.get("category_id") else None,
            category_name=cat.get("description_translated") or cat.get("description") or "Geral",
            due_day=exp.get("due_day") or 1,
            due_date=due_date,
            reference_month=item.get("reference_month") or "",
            amount=float(item.get("amount") or 0),
            status=status,
            paid_at=item.get("paid_at"),
            installment_number=item.get("installment_number"),
            total_installments=exp.get("total_installments"),
            is_overdue=is_overdue,
            is_stacked=is_stacked
        )

    def obter_dashboard(self, user_id: str, mes: Optional[str] = None) -> PaymentsDashboardResponse:
        ref_month = mes or date.today().strftime("%Y-%m")
        
        pagamentos_raw = self.repository.obter_pagamentos_mes(user_id, ref_month)
        pendencias_raw = self.repository.obter_pendencias_anteriores(user_id, ref_month)
        meses_disponiveis = self.repository.obter_meses_disponiveis(user_id)

        pagamentos_mes = [self._formatar_pagamento(p, is_stacked=False) for p in pagamentos_raw]
        pendencias_anteriores = [self._formatar_pagamento(p, is_stacked=True) for p in pendencias_raw]

        todos_mes = pagamentos_mes + pendencias_anteriores
        total_a_pagar = sum(p.amount for p in pagamentos_mes)
        total_em_aberto = sum(p.amount for p in todos_mes if p.status == "pending")
        total_pago = sum(p.amount for p in pagamentos_mes if p.status == "paid")
        total_em_atraso = sum(p.amount for p in todos_mes if p.is_overdue)

        return PaymentsDashboardResponse(
            mes=ref_month,
            meses_disponiveis=meses_disponiveis,
            kpis=PaymentsKPIs(
                total_a_pagar_mes=round(total_a_pagar, 2),
                total_em_aberto=round(total_em_aberto, 2),
                total_pago=round(total_pago, 2),
                total_em_atraso=round(total_em_atraso, 2)
            ),
            pendencias_anteriores=pendencias_anteriores,
            pagamentos_mes=pagamentos_mes
        )

    def criar_despesa(self, user_id: str, payload: ExpenseCreate) -> dict:
        return self.repository.criar_despesa_recorrente(user_id, payload.dict())

    def atualizar_valor_mensal(self, monthly_id: str, user_id: str, payload: MonthlyPaymentUpdate) -> dict:
        return self.repository.atualizar_valor_mensal(monthly_id, user_id, payload.amount)

    def alternar_status_pagamento(self, monthly_id: str, user_id: str) -> dict:
        res = self.repository.alternar_pagamento(monthly_id, user_id)
        return {
            "id": res["id"],
            "novo_status": res["status"],
            "paid_at": res.get("paid_at")
        }

    def excluir_despesa(self, expense_id: str, user_id: str, mes: str):
        self.repository.excluir_despesa_recorrente(expense_id, user_id, mes)

    def obter_historico(self, user_id: str, ano: int) -> HistoryResponse:
        historico = self.repository.obter_historico_ano(user_id, ano)
        return HistoryResponse(historico=historico)