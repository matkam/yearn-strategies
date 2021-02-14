from brownie import Wei, Contract

sethKey = 0x7345544800000000000000000000000000000000000000000000000000000000  # "sETH"
susdKey = 0x7355534400000000000000000000000000000000000000000000000000000000  # "sUSD"
exchangerKey = 0x45786368616E6765720000000000000000000000000000000000000000000000  # "Exchanger"
delegateApprovalsKey = 0x44656C6567617465417070726F76616C73000000000000000000000000000000  # "DelegateApprovals"


def test_zap(accounts, ZapYvecrvSusd, vault_ecrv_live, interface, chain):
    whale = accounts.at("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", force=True)
    zap = whale.deploy(ZapYvecrvSusd)
    # zap = Contract("0x85dB618d507909570299d3e3cFfD0FC4D4F97FeF")
    sEth = Contract(zap.sEth())
    sUsd = Contract(zap.sUsd())
    synthetixResolver = Contract(zap.synthetixResolver())
    synthetixExchanger = Contract(synthetixResolver.getAddress(exchangerKey))
    delegateApprovals = Contract(synthetixResolver.getAddress(delegateApprovalsKey))

    delegateApprovals.approveExchangeOnBehalf(zap, {"from": whale})
    sEth.approve(zap, 2 ** 256 - 1, {"from": whale})
    # sEth.approve(whale, 2 ** 256 - 1, {"from": whale})
    sUsd.approve(zap, 2 ** 256 - 1, {"from": whale})

    vault_ecrv_live.approve(zap, 2 ** 256 - 1, {"from": whale})

    print("Zap In 100 ETH eCRV estimates")
    print("----------------------------")
    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("100 ether"), 0) / Wei("1 ether")
    print(f"  0% swap: {lpTokenEstimate} eCRV")

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("100 ether"), 50) / Wei("1 ether")
    print(f" 50% swap: {lpTokenEstimate} eCRV")

    lpTokenEstimate = zap.estimateZapInWithSwap(Wei("100 ether"), 100) / Wei("1 ether")
    print(f"100% swap: {lpTokenEstimate} eCRV")

    print("")
    print("Zap In 100 ETH actuals")
    print("----------------------------")

    zap.swapEthToSeth({"from": whale, "value": Wei("50 ether")})
    sethBalance = sEth.balanceOf(whale) / Wei("1 ether")
    print(f"sETH actual, 50% swap: {sethBalance} sETH")

    waitLeft = synthetixExchanger.maxSecsLeftInWaitingPeriod(whale.address, sethKey)
    print(f"> Waiting period: {waitLeft} seconds")
    chain.sleep(waitLeft)
    chain.mine(1)

    sethBalance = sEth.balanceOf(whale)
    sEth.approve(whale, sethBalance, {"from": zap})  # this is a workaround for a bug
    zap.zapIn(sethBalance, {"value": Wei("50 ether"), "from": whale})

    yvecrvBalance = vault_ecrv_live.balanceOf(whale) / Wei("1 ether")
    print(f"Vault tokens: {yvecrvBalance} yveCRV")

    ### Zap Out ###

    print("")
    print("Zap Out 100 yveCRV to ETH estimates")
    print("----------------------------")
    ethEstimate = zap.estimateZapOutWithSwap(Wei("100 ether"), 0) / Wei("1 ether")
    print(f"  0% swap: {ethEstimate} ETH")

    ethEstimate = zap.estimateZapOutWithSwap(Wei("100 ether"), 50) / Wei("1 ether")
    print(f" 50% swap: {ethEstimate} ETH")

    ethEstimate = zap.estimateZapOutWithSwap(Wei("100 ether"), 100) / Wei("1 ether")
    print(f"100% swap: {ethEstimate} ETH")

    print("")
    print("Zap Out all yveCRV actuals")
    print("----------------------------")

    startingEthBalance = whale.balance()
    zap.zapOut(2 ** 256 - 1, 50, {"from": whale})
    zappedOutEth = (whale.balance() - startingEthBalance) / Wei("1 ether")
    susdBalance = sUsd.balanceOf(whale)
    susdBalancePretty = susdBalance / Wei("1 ether")
    print(f"actuals, 50% swap: {zappedOutEth} ETH, {susdBalancePretty} sUSD")

    waitLeft = synthetixExchanger.maxSecsLeftInWaitingPeriod(whale.address, susdKey)
    print(f"> Waiting period: {waitLeft} seconds")
    chain.sleep(waitLeft)
    chain.mine(1)

    zap.swapSusdToEth(susdBalance, {"from": whale})
    zappedOutEth = (whale.balance() - startingEthBalance) / Wei("1 ether")
    print(f"Zap out total: {zappedOutEth} ETH")

