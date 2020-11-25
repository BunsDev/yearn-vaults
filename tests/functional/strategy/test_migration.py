import brownie


def test_good_migration(
    chain, token, strategy, vault, gov, strategist, guardian, TestStrategy, rando
):
    # Call this once to seed the strategy with debt
    chain.sleep(1)  # Reverts if no delta time
    strategy.harvest({"from": strategist})

    strategy_debt = vault.strategies(strategy).dict()["totalDebt"]
    assert strategy_debt == token.balanceOf(strategy)

    new_strategy = strategist.deploy(TestStrategy, vault)
    assert vault.strategies(new_strategy).dict()["totalDebt"] == 0
    assert token.balanceOf(new_strategy) == 0

    # Only Governance can migrate
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": rando})
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": strategist})
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": guardian})

    vault.migrateStrategy(strategy, new_strategy, {"from": gov})
    assert (
        vault.strategies(strategy).dict()["totalDebt"] == token.balanceOf(strategy) == 0
    )
    assert (
        vault.strategies(new_strategy).dict()["totalDebt"]
        == token.balanceOf(new_strategy)
        == strategy_debt
    )

    # Also, governance can migrate directly
    new_strategy.migrate(strategy, {"from": gov})


def test_bad_migration(
    token, vault, strategy, gov, strategist, TestStrategy, Vault, rando
):
    different_vault = gov.deploy(Vault, token, gov, gov, "", "")
    new_strategy = strategist.deploy(TestStrategy, different_vault)

    # Can't migrate to a strategy with a different vault
    with brownie.reverts():
        vault.migrateStrategy(strategy, new_strategy, {"from": gov})

    new_strategy = strategist.deploy(TestStrategy, vault)

    # Can't migrate if you're not the Vault  or governance
    with brownie.reverts():
        strategy.migrate(new_strategy, {"from": rando})
