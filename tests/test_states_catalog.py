from app.states import list_states


def test_list_states_returns_catalog_ordered_by_sort_order():
    states = list_states()

    assert [state.code for state in states] == [
        "PENDIENTE",
        "EN_CURSO",
        "BLOQUEADA",
        "HECHA",
    ]
