"""
Router para o módulo Receivables (A Receber).
Define todos os endpoints HTTP da API.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from .schemas import (
    ReceivablePeopleCreate,
    ReceivablePeopleResponse,
    CardSplitCreate,
    CardSplitResponse,
    ManualDebtCreate,
    ManualDebtUpdate,
    ManualDebtResponse,
    ReceivableSummaryItem,
    PersonDetailResponse,
    CardTransactionForAllocation,
)
from .service import (
    ReceivablePeopleService,
    CardSplitService,
    ManualDebtService,
    ReceivableSummaryService,
)


router = APIRouter(prefix="/api/v1/receivables", tags=["receivables"])

USER_ID = "d262bc6c-d58b-4f4e-99b4-505202b646ba"


# ============================================================================
# Endpoints para Pessoas (Receivable People)
# ============================================================================

@router.get("/summary", response_model=list[ReceivableSummaryItem])
def get_receivable_summary(
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    user_id: str = Query(USER_ID),
):
    """
    Retorna a lista de pessoas com o total de cartão no mês e o saldo devedor manual.

    Query Parameters:
    - mes: Mês no formato YYYY-MM
    """
    try:
        summary = ReceivableSummaryService.get_summary_for_user(user_id, mes)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/people/{person_id}", response_model=PersonDetailResponse)
def get_person_detail(
    person_id: str,
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    user_id: str = Query(USER_ID),
):
    """
    Traz os detalhes da pessoa, incluindo card_splits do mês e histórico de manual_debts.

    Path Parameters:
    - person_id: ID da pessoa

    Query Parameters:
    - mes: Mês no formato YYYY-MM
    """
    try:
        person = ReceivablePeopleService.get_person(person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        detail = ReceivableSummaryService.get_person_detail(person_id, mes)
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/people", response_model=ReceivablePeopleResponse)
def create_person(
    payload: ReceivablePeopleCreate,
    user_id: str = Query(USER_ID),
):
    """Cadastra uma nova pessoa vinculada ao user_id."""
    try:
        person = ReceivablePeopleService.create_person(user_id, payload.name)
        return person
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/people/{person_id}", response_model=ReceivablePeopleResponse)
def update_person(
    person_id: str,
    payload: ReceivablePeopleCreate,
    user_id: str = Query(USER_ID),
):
    """Atualiza os dados de uma pessoa."""
    try:
        person = ReceivablePeopleService.get_person(person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        updated = ReceivablePeopleService.update_person(person_id, payload.name)
        if not updated:
            raise HTTPException(status_code=400, detail="Falha ao atualizar pessoa")

        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/people/{person_id}")
def delete_person(
    person_id: str,
    user_id: str = Query(USER_ID),
):
    """Deleta uma pessoa (cascata remove card_splits e manual_debts)."""
    try:
        person = ReceivablePeopleService.get_person(person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        success = ReceivablePeopleService.delete_person(person_id)
        if not success:
            raise HTTPException(status_code=400, detail="Falha ao deletar pessoa")

        return {"message": "Pessoa deletada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Endpoints para Compras de Cartão (Card Transactions)
# ============================================================================

@router.get("/people/{person_id}/card-months")
def get_person_card_months(
    person_id: str,
    user_id: str = Query(USER_ID),
):
    """Retorna os meses com card_splits para uma pessoa."""
    try:
        person = ReceivablePeopleService.get_person(person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        months = ReceivableSummaryService.get_available_months(person_id)
        return {"months": months}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/people/{person_id}/card-transactions", response_model=list[CardTransactionForAllocation])
def get_available_card_transactions(
    person_id: str,
    mes: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    busca: Optional[str] = Query(None),
    card_id: Optional[str] = Query(None),
    user_id: str = Query(USER_ID),
):
    """
    Lista compras da fatura filtradas disponíveis para alocação.

    Path Parameters:
    - person_id: ID da pessoa

    Query Parameters:
    - mes: Mês no formato YYYY-MM
    - busca: Texto para filtrar por descrição (opcional)
    - card_id: ID do cartão para filtrar (opcional)
    """
    try:
        person = ReceivablePeopleService.get_person(person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        transactions = ReceivableSummaryService.get_available_transactions_for_allocation(
            person_id, mes, busca, card_id
        )
        return transactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Endpoints para Divisão de Cartão (Card Splits)
# ============================================================================

@router.post("/card-splits", response_model=CardSplitResponse)
def create_or_update_card_split(
    payload: CardSplitCreate,
    user_id: str = Query(USER_ID),
):
    """
    Vincula ou edita a divisão de uma compra de cartão para a pessoa.

    Se já existe uma divisão para a mesma transação, pessoa e mês, ela será atualizada.
    """
    try:
        person = ReceivablePeopleService.get_person(payload.person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        split = CardSplitService.allocate_transaction(
            payload.transaction_id,
            payload.person_id,
            payload.reference_month,
            payload.is_integral,
            payload.amount_person,
            payload.total_transaction_amount,
        )
        return split
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/card-splits/{split_id}")
def remove_card_split(
    split_id: str,
    user_id: str = Query(USER_ID),
):
    """Remove o vínculo de uma compra."""
    try:
        from .repository import CardSplitRepository
        split = CardSplitRepository.get_by_id(split_id)
        if not split:
            raise HTTPException(status_code=404, detail="Divisão não encontrada")

        person = ReceivablePeopleService.get_person(split.person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        success = CardSplitService.remove_allocation(split_id)
        if not success:
            raise HTTPException(status_code=400, detail="Falha ao remover divisão")

        return {"message": "Divisão removida com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Endpoints para Lançamentos Manuais (Manual Debts)
# ============================================================================

@router.post("/manual", response_model=ManualDebtResponse)
def create_manual_debt(
    payload: ManualDebtCreate,
    user_id: str = Query(USER_ID),
):
    """Registra uma nova cobrança (charge) ou pagamento (payment)."""
    try:
        person = ReceivablePeopleService.get_person(payload.person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=404, detail="Pessoa não encontrada")

        if payload.type == "charge":
            debt = ManualDebtService.record_charge(
                payload.person_id,
                payload.amount,
                payload.description,
            )
        elif payload.type == "payment":
            debt = ManualDebtService.record_payment(
                payload.person_id,
                payload.amount,
                payload.description,
            )
        else:
            raise HTTPException(status_code=400, detail="Tipo inválido (use 'charge' ou 'payment')")

        return debt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/manual/{debt_id}", response_model=ManualDebtResponse)
def update_manual_debt(
    debt_id: str,
    payload: ManualDebtUpdate,
    user_id: str = Query(USER_ID),
):
    """Atualiza o valor ou a descrição de um lançamento manual."""
    try:
        from .repository import ManualDebtRepository
        debt = ManualDebtRepository.get_by_id(debt_id)
        if not debt:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")

        person = ReceivablePeopleService.get_person(debt.person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        updated = ManualDebtService.update_debt(
            debt_id,
            payload.type,
            payload.amount,
            payload.description,
        )

        if not updated:
            raise HTTPException(status_code=400, detail="Falha ao atualizar lançamento")

        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/manual/{debt_id}")
def delete_manual_debt(
    debt_id: str,
    user_id: str = Query(USER_ID),
):
    """Exclui um lançamento manual."""
    try:
        from .repository import ManualDebtRepository
        debt = ManualDebtRepository.get_by_id(debt_id)
        if not debt:
            raise HTTPException(status_code=404, detail="Lançamento não encontrado")

        person = ReceivablePeopleService.get_person(debt.person_id)
        if not person or person.user_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado")

        success = ManualDebtService.delete_debt(debt_id)
        if not success:
            raise HTTPException(status_code=400, detail="Falha ao deletar lançamento")

        return {"message": "Lançamento deletado com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
