"""
Repository para o módulo Receivables (A Receber).
Acesso aos dados no Supabase.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.core.database import supabase
from .schemas import (
    ReceivablePeopleCreate,
    ReceivablePeopleResponse,
    CardSplitCreate,
    CardSplitResponse,
    CardSplitWithTransactionDetails,
    ManualDebtCreate,
    ManualDebtResponse,
    ManualDebtUpdate,
)


class ReceivablePeopleRepository:
    """Repository para gerenciar pessoas do módulo A Receber."""

    @staticmethod
    def create(user_id: str, name: str) -> ReceivablePeopleResponse:
        """Cria uma nova pessoa."""
        response = supabase.table("receivable_people").insert({
            "user_id": user_id,
            "name": name,
        }).execute()
        
        if response.data:
            data = response.data[0]
            return ReceivablePeopleResponse(**data)
        raise ValueError("Falha ao criar pessoa")

    @staticmethod
    def get_by_id(person_id: str) -> Optional[ReceivablePeopleResponse]:
        """Obtém uma pessoa pelo ID."""
        response = supabase.table("receivable_people").select("*").eq("id", person_id).single().execute()
        
        if response.data:
            return ReceivablePeopleResponse(**response.data)
        return None

    @staticmethod
    def list_by_user(user_id: str) -> list[ReceivablePeopleResponse]:
        """Lista todas as pessoas de um usuário."""
        response = supabase.table("receivable_people").select("*").eq("user_id", user_id).execute()
        
        return [ReceivablePeopleResponse(**item) for item in response.data]

    @staticmethod
    def update(person_id: str, name: str) -> Optional[ReceivablePeopleResponse]:
        """Atualiza os dados de uma pessoa."""
        response = supabase.table("receivable_people").update({
            "name": name,
        }).eq("id", person_id).execute()
        
        if response.data:
            return ReceivablePeopleResponse(**response.data[0])
        return None

    @staticmethod
    def delete(person_id: str) -> bool:
        """Deleta uma pessoa (cascata remove card_splits e manual_debts)."""
        response = supabase.table("receivable_people").delete().eq("id", person_id).execute()
        return len(response.data) > 0 if response.data else True


class CardSplitRepository:
    """Repository para gerenciar divisões de cartão."""

    @staticmethod
    def create_or_update(
        transaction_id: str,
        person_id: str,
        reference_month: str,
        is_integral: bool,
        amount_person: Decimal,
        total_transaction_amount: Decimal,
    ) -> CardSplitResponse:
        """Cria ou atualiza uma divisão de cartão.
        
        Se já existe uma divisão para a mesma transação, pessoa e mês,
        atualiza o registro. Caso contrário, cria um novo.
        """
        # Tenta encontrar divisão existente
        response = supabase.table("card_splits").select("id").eq(
            "transaction_id", transaction_id
        ).eq("person_id", person_id).eq("reference_month", reference_month).execute()

        data = {
            "is_integral": is_integral,
            "amount_person": float(amount_person),
            "total_transaction_amount": float(total_transaction_amount),
        }

        if response.data:
            # Atualiza
            result = supabase.table("card_splits").update(data).eq(
                "id", response.data[0]["id"]
            ).execute()
        else:
            # Cria novo
            data.update({
                "transaction_id": transaction_id,
                "person_id": person_id,
                "reference_month": reference_month,
            })
            result = supabase.table("card_splits").insert(data).execute()

        if result.data:
            return CardSplitResponse(**result.data[0])
        raise ValueError("Falha ao criar/atualizar divisão de cartão")

    @staticmethod
    def get_by_id(split_id: str) -> Optional[CardSplitResponse]:
        """Obtém uma divisão pelo ID."""
        response = supabase.table("card_splits").select("*").eq("id", split_id).single().execute()
        
        if response.data:
            return CardSplitResponse(**response.data)
        return None

    @staticmethod
    def get_by_person_and_month(
        person_id: str,
        reference_month: str,
    ) -> list[CardSplitWithTransactionDetails]:
        """Lista divisões de uma pessoa em um mês específico com detalhes da transação."""
        # Busca card_splits
        response = supabase.table("card_splits").select("*").eq(
            "person_id", person_id
        ).eq("reference_month", reference_month).execute()

        splits = response.data if response.data else []

        # Enriquece com detalhes da transação
        results = []
        for split in splits:
            trans_response = supabase.table("transactions").select(
                "id, description, date, cards(*, items(*))"
            ).eq("id", split["transaction_id"]).single().execute()

            if trans_response.data:
                trans_data = trans_response.data
                card_data = trans_data.get("cards") or {}
                item_data = card_data.get("items") or {}
                bank_name = item_data.get("bank_name") or card_data.get("name") or "Cartão"

                split_data = CardSplitWithTransactionDetails(
                    **split,
                    description=trans_data.get("description"),
                    date=trans_data.get("date"),
                    bank=bank_name,
                )
                results.append(split_data)

        return results

    @staticmethod
    def get_sum_by_person_and_month(person_id: str, reference_month: str) -> Decimal:
        """Calcula a soma de amount_person para uma pessoa em um mês."""
        response = supabase.table("card_splits").select("amount_person").eq(
            "person_id", person_id
        ).eq("reference_month", reference_month).execute()

        total = Decimal("0")
        for item in (response.data or []):
            total += Decimal(str(item.get("amount_person", 0)))
        
        return total

    @staticmethod
    def get_splits_by_transaction(transaction_id: str) -> list[CardSplitResponse]:
        """Lista todas as divisões de uma transação."""
        response = supabase.table("card_splits").select("*").eq(
            "transaction_id", transaction_id
        ).execute()

        return [CardSplitResponse(**item) for item in (response.data or [])]

    @staticmethod
    def delete(split_id: str) -> bool:
        """Deleta uma divisão de cartão."""
        response = supabase.table("card_splits").delete().eq("id", split_id).execute()
        return len(response.data) > 0 if response.data else True


class ManualDebtRepository:
    """Repository para gerenciar lançamentos manuais."""

    @staticmethod
    def create(person_id: str, debt_type: str, amount: Decimal, description: Optional[str] = None) -> ManualDebtResponse:
        """Cria um novo lançamento manual."""
        response = supabase.table("manual_debts").insert({
            "person_id": person_id,
            "type": debt_type,
            "amount": float(amount),
            "description": description,
        }).execute()

        if response.data:
            return ManualDebtResponse(**response.data[0])
        raise ValueError("Falha ao criar lançamento manual")

    @staticmethod
    def get_by_id(debt_id: str) -> Optional[ManualDebtResponse]:
        """Obtém um lançamento pelo ID."""
        response = supabase.table("manual_debts").select("*").eq("id", debt_id).single().execute()
        
        if response.data:
            return ManualDebtResponse(**response.data)
        return None

    @staticmethod
    def get_by_person(person_id: str, limit: int = 1000) -> list[ManualDebtResponse]:
        """Lista todos os lançamentos de uma pessoa."""
        response = supabase.table("manual_debts").select("*").eq(
            "person_id", person_id
        ).order("occurred_at", desc=True).limit(limit).execute()

        return [ManualDebtResponse(**item) for item in (response.data or [])]

    @staticmethod
    def get_sum_by_person(person_id: str) -> Decimal:
        """Calcula o saldo manual de uma pessoa (charges - payments)."""
        response = supabase.table("manual_debts").select("type, amount").eq(
            "person_id", person_id
        ).execute()

        total_charges = Decimal("0")
        total_payments = Decimal("0")

        for item in (response.data or []):
            amount = Decimal(str(item.get("amount", 0)))
            if item.get("type") == "charge":
                total_charges += amount
            elif item.get("type") == "payment":
                total_payments += amount

        balance = total_charges - total_payments
        # Saldo nunca fica abaixo de zero
        return max(balance, Decimal("0"))

    @staticmethod
    def update(debt_id: str, debt_type: Optional[str] = None, amount: Optional[Decimal] = None, description: Optional[str] = None) -> Optional[ManualDebtResponse]:
        """Atualiza um lançamento manual."""
        update_data = {}
        if debt_type is not None:
            update_data["type"] = debt_type
        if amount is not None:
            update_data["amount"] = float(amount)
        if description is not None:
            update_data["description"] = description

        if not update_data:
            return ManualDebtRepository.get_by_id(debt_id)

        response = supabase.table("manual_debts").update(update_data).eq("id", debt_id).execute()
        
        if response.data:
            return ManualDebtResponse(**response.data[0])
        return None

    @staticmethod
    def delete(debt_id: str) -> bool:
        """Deleta um lançamento manual."""
        response = supabase.table("manual_debts").delete().eq("id", debt_id).execute()
        return len(response.data) > 0 if response.data else True
