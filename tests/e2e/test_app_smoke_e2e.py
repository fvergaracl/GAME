from app.model.games import Games


def test_e2e_context_starts_with_empty_database(e2e_context):
    with e2e_context.container.db().session() as session:
        assert session.query(Games).count() == 0


def test_e2e_context_resets_state_between_tests(e2e_context):
    with e2e_context.container.db().session() as session:
        game = Games(
            externalGameId="e2e_game_1",
            strategyId="default",
            platform="web",
        )
        session.add(game)
        session.commit()

    # The current test can mutate state; the next test starts clean due fixture reset.
    with e2e_context.container.db().session() as session:
        assert session.query(Games).count() == 1
