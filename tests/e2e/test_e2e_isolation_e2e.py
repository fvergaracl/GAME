from app.model.games import Games


def test_database_is_clean_on_new_test(e2e_context):
    with e2e_context.container.db().session() as session:
        assert session.query(Games).count() == 0
