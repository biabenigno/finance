"""
Service para o módulo Receivables (A Receber).
Contém as regras de negócio e validações.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.core.database import supabase
from app.modules.invoices.repository import InvoiceRepository
from .repository import (
    ReceivablePeopleRepository,
    CardSplitRepository,
    ManualDebtRepository,
)
from .schemas import (
    ReceivablePeopleResponse,
    CardSplitResponse,
    ManualDebtResponse,
    ReceivableSummaryItem,
    PersonDetailResponse,
    CardTransactionForAllocation,
)


class ReceivablePeopleService:
    """Serviço para gerenciamento de pessoas."""

    @staticmethod
    def create_person(user_id: str, name: str) -> ReceivablePeopleResponse:
        """Cria uma nova pessoa."""
        return ReceivablePeopleRepository.create(user_id, name)

    @staticmethod
    def get_person(person_id: str) -> Optional[ReceivablePeopleResponse]:
        """Obtém os dados de uma pessoa."""
        return ReceivablePeopleRepository.get_by_id(person_id)

    @staticmethod
    def list_people(user_id: str) -> list[ReceivablePeopleResponse]:
        """Lista pessoas de um usuário."""
        return ReceivablePeopleRepository.list_by_user(user_id)

    @staticmethod
    def update_person(person_id: str, name: str) -> Optional[ReceivablePeopleResponse]:
        """Atualiza os dados de uma pessoa."""
        return ReceivablePeopleRepository.update(person_id, name)

    @staticmethod
    def delete_person(person_id: str) -> bool:
        """Deleta uma pessoa e todos os seus registros relacionados."""
        return ReceivablePeopleRepository.delete(person_id)


class CardSplitService:
    """Serviço para gerenciamento de divisões de cartão."""

    @staticmethod
    def validate_allocation(
        transaction_id: str,
        amount_person: Decimal,
        total_transaction_amount: Decimal,
    ) -> tuple[bool, Optional[str]]:
        """Valida se a alocação está dentro dos limites.
        
        Retorna:
            (True, None) se válido
            (False, mensagem_erro) se inválido
        """
        # Verifica se o valor da pessoa não excede o total
        if amount_person > total_transaction_amount:
            return False, "Valor da pessoa não pode exceder o valor total da compra"

        # Busca todas as divisões da transação
        existing_splits = CardSplitRepository.get_splits_by_transaction(transaction_id)

        # Calcula a soma das divisões já atribuídas (excluindo a que será atualizada)
        total_allocated = sum(
            Decimal(str(split.amount_person)) for split in existing_splits
        )

        # Soma a nova alocação
        new_total = total_allocated + amount_person

        if new_total > total_transaction_amount:
            return False, (
                f"Soma das divisões não pode exceder o valor total da compra. "
                f"Já alocado: {total_allocated}, novo: {amount_person}"
            )

        return True, None

    @staticmethod
    def allocate_transaction(
        transaction_id: str,
        person_id: str,
        reference_month: str,
        is_integral: bool,
        amount_person: Decimal,
        total_transaction_amount: Decimal,
    ) -> CardSplitResponse:
        """Aloca uma compra de cartão para uma pessoa.
        
        Se já existe uma alocação para a mesma transação, pessoa e mês,
        ela será atualizada.
        """
        # Valida a alocação
        is_valid, error_msg = CardSplitService.validate_allocation(
            transaction_id,
            amount_person,
            total_transaction_amount,
        )

        if not is_valid:
            raise ValueError(error_msg)

        # Cria ou atualiza
        return CardSplitRepository.create_or_update(
            transaction_id,
            person_id,
            reference_month,
            is_integral,
            amount_person,
            total_transaction_amount,
        )

    @staticmethod
    def get_person_card_total(person_id: str, reference_month: str) -> Decimal:
        """Calcula o total de cartão para uma pessoa em um mês."""
        return CardSplitRepository.get_sum_by_person_and_month(person_id, reference_month)

    @staticmethod
    def get_person_card_splits(
        person_id: str,
        reference_month: str,
    ):
        """Lista todas as divisões de uma pessoa em um mês."""
        return CardSplitRepository.get_by_person_and_month(person_id, reference_month)

    @staticmethod
    def remove_allocation(split_id: str) -> bool:
        """Remove uma alocação de cartão."""
        return CardSplitRepository.delete(split_id)


class ManualDebtService:
    """Serviço para gerenciamento de saldo manual."""

    @staticmethod
    def validate_amount(amount: Decimal) -> tuple[bool, Optional[str]]:
        """Valida o valor de uma transação manual."""
        if amount <= 0:
            return False, "Valor deve ser maior que zero"
        return True, None

    @staticmethod
    def record_charge(
        person_id: str,
        amount: Decimal,
        description: Optional[str] = None,
    ) -> ManualDebtResponse:
        """Registra uma cobrança para uma pessoa."""
        is_valid, error_msg = ManualDebtService.validate_amount(amount)
        if not is_valid:
            raise ValueError(error_msg)

        return ManualDebtRepository.create(person_id, "charge", amount, description)

    @staticmethod
    def record_payment(
        person_id: str,
        amount: Decimal,
        description: Optional[str] = None,
    ) -> ManualDebtResponse:
        """Registra um pagamento para uma pessoa."""
        is_valid, error_msg = ManualDebtService.validate_amount(amount)
        if not is_valid:
            raise ValueError(error_msg)

        return ManualDebtRepository.create(person_id, "payment", amount, description)

    @staticmethod
    def get_person_debts(person_id: str) -> list[ManualDebtResponse]:
        """Lista todos os lançamentos de uma pessoa."""
        return ManualDebtRepository.get_by_person(person_id)

    @staticmethod
    def get_person_manual_balance(person_id: str) -> Decimal:
        """Calcula o saldo manual de uma pessoa (charges - payments, nunca negativo)."""
        return ManualDebtRepository.get_sum_by_person(person_id)

    @staticmethod
    def update_debt(
        debt_id: str,
        debt_type: Optional[str] = None,
        amount: Optional[Decimal] = None,
        description: Optional[str] = None,
    ) -> Optional[ManualDebtResponse]:
        """Atualiza um lançamento manual."""
        if amount is not None:
            is_valid, error_msg = ManualDebtService.validate_amount(amount)
            if not is_valid:
                raise ValueError(error_msg)

        return ManualDebtRepository.update(debt_id, debt_type, amount, description)

    @staticmethod
    def delete_debt(debt_id: str) -> bool:
        """Deleta um lançamento manual."""
        return ManualDebtRepository.delete(debt_id)


class ReceivableSummaryService:
    """Serviço para gerar resumos consolidados."""

    @staticmethod
    def get_summary_for_user(user_id: str, reference_month: str) -> list[ReceivableSummaryItem]:
        """Gera o resumo de A Receber para um usuário em um mês específico.
        
        Para cada pessoa, calcula:
        - card_total: soma de amount_person das divisões do mês
        - manual_total: saldo de charges - payments (nunca negativo)
        """
        people = ReceivablePeopleRepository.list_by_user(user_id)
        summary = []

        for person in people:
            card_total = CardSplitService.get_person_card_total(person.id, reference_month)
            manual_total = ManualDebtService.get_person_manual_balance(person.id)

            summary.append(ReceivableSummaryItem(
                id=person.id,
                name=person.name,
                card_total=card_total,
                manual_total=manual_total,
            ))

        return summary

    @staticmethod
    def get_person_detail(person_id: str, reference_month: str) -> PersonDetailResponse:
        """Obtém os detalhes completos de uma pessoa para um mês específico."""
        person = ReceivablePeopleRepository.get_by_id(person_id)
        if not person:
            raise ValueError(f"Pessoa {person_id} não encontrada")

        # Busca os dados
        card_total = CardSplitService.get_person_card_total(person_id, reference_month)
        manual_total = ManualDebtService.get_person_manual_balance(person_id)
        card_splits = CardSplitService.get_person_card_splits(person_id, reference_month)
        manual_debts = ManualDebtService.get_person_debts(person_id)

        # Busca os meses disponíveis
        available_months = ReceivableSummaryService.get_available_months(person_id)

        return PersonDetailResponse(
            id=person.id,
            name=person.name,
            card_total=card_total,
            manual_total=manual_total,
            card_splits=card_splits,
            manual_debts=manual_debts,
            available_months=available_months,
        )

    @staticmethod
    def get_available_months(person_id: str, user_id: Optional[str] = None) -> list[str]:
        """Obtém os meses disponíveis (faturas cadastradas e meses com card_splits)."""
        mes_atual = datetime.now().strftime("%Y-%m")
        months_set = {mes_atual}

        # Meses com card_splits já existentes
        response = supabase.table("card_splits").select(
            "reference_month"
        ).eq("person_id", person_id).execute()

        if response.data:
            for item in response.data:
                if item.get("reference_month"):
                    months_set.add(item["reference_month"])

        # Se tiver user_id ou se buscar pessoa para pegar user_id, inclui meses de faturas reais
        uid = user_id
        if not uid:
            p = ReceivablePeopleRepository.get_by_id(person_id)
            if p:
                uid = p.user_id

        if uid:
            faturas = InvoiceRepository.listar_faturas_usuario(uid)
            for f in faturas:
                if f.get("due_date"):
                    months_set.add(f["due_date"][:7])

        return sorted(months_set, reverse=True)

    @staticmethod
    def get_available_transactions_for_allocation(
        person_id: str,
        reference_month: str,
        search: Optional[str] = None,
        card_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> list[CardTransactionForAllocation]:
        """Lista compras de cartão da fatura selecionada (e fatura aberta caso seja o mês atual).
        
        Retorna transações não desconsideradas, com suporte a busca por texto ou valor.
        """
        uid = user_id
        if not uid:
            p = ReceivablePeopleRepository.get_by_id(person_id)
            if p:
                uid = p.user_id

        if not uid:
            return []

        mes_atual = datetime.now().strftime("%Y-%m")
        raw_txs = []

        # Se for o mês atual, inclui as transações em aberto
        if reference_month == mes_atual:
            raw_txs.extend(InvoiceRepository.listar_transacoes(uid, "atual", card_id))

        # Inclui as transações vinculadas à fatura do mês de referência
        raw_txs.extend(InvoiceRepository.listar_transacoes(uid, reference_month, card_id))

        # Se ainda não houver transações (ex: compras ainda sem fatura ou fatura fora da data),
        # busca transações do mês pela data como fallback
        if not raw_txs:
            query = supabase.table("transactions").select(
                "id, description, amount, date, card_id, is_ignored, cards(*, items(*))"
            ).eq("is_ignored", False)
            if card_id:
                query = query.eq("card_id", card_id)
            resp = query.order("date", desc=True).execute()
            all_db = resp.data or []
            for t in all_db:
                if t.get("date") and str(t["date"])[:7] == reference_month:
                    raw_txs.append(t)

        # Deduplica por ID preservando ordem
        seen = set()
        transactions = []
        for tx in raw_txs:
            if tx["id"] not in seen:
                seen.add(tx["id"])
                transactions.append(tx)

        # Normaliza busca se fornecida (texto ou valor numérico)
        search_term = search.strip().lower() if search else None
        search_val_normalized = None
        if search_term:
            val_clean = search_term.replace("r$", "").replace(" ", "").replace(".", "").replace(",", ".")
            try:
                search_val_normalized = float(val_clean)
            except ValueError:
                search_val_normalized = None

        # Filtra transações desconsideradas e aplica busca
        filtered_transactions = []
        for trans in transactions:
            if trans.get("is_ignored"):
                continue

            if search_term:
                desc = str(trans.get("description", "")).lower()
                amount_float = float(trans.get("amount", 0))
                amount_str = f"{amount_float:.2f}".replace(".", ",")
                amount_str_dot = f"{amount_float:.2f}"

                match_desc = search_term in desc
                match_val = False
                if search_val_normalized is not None and abs(amount_float - search_val_normalized) < 0.001:
                    match_val = True
                elif search_term in amount_str or search_term in amount_str_dot:
                    match_val = True

                if not (match_desc or match_val):
                    continue

            filtered_transactions.append(trans)

        # Busca card_splits para esta pessoa
        splits_response = supabase.table("card_splits").select(
            "transaction_id, is_integral"
        ).eq("person_id", person_id).execute()

        linked_transactions = {
            split["transaction_id"]: split["is_integral"]
            for split in (splits_response.data or [])
        }

        # Monta a resposta
        result = []
        for trans in filtered_transactions:
            is_linked = trans["id"] in linked_transactions
            card_data = trans.get("cards") or {}
            item_data = card_data.get("items") or {}
            bank_name = item_data.get("bank_name") or card_data.get("name") or "Cartão"
            c_name = card_data.get("name") or bank_name

            result.append(CardTransactionForAllocation(
                id=trans["id"],
                description=trans.get("description", ""),
                amount=Decimal(str(trans.get("amount", 0))),
                date=trans.get("date"),
                bank=bank_name,
                card_name=c_name,
                card_id=trans.get("card_id"),
                is_linked=is_linked,
                linked_to_person=is_linked,
            ))

        return result
