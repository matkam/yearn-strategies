from brownie import Wei, web3

sethKey = 0x7345544800000000000000000000000000000000000000000000000000000000
susdKey = 0x7355534400000000000000000000000000000000000000000000000000000000


def test_zap(accounts, ZapYvecrvSusd, vault_ecrv_live, interface, chain):
    whale = accounts.at("0xbe0eb53f46cd790cd13851d5eff43d12404d33e8", force=True)
    zap = whale.deploy(ZapYvecrvSusd)
    sEth = interface.ISynth(zap.sEth())
    sUsd = interface.ISynth(zap.sUsd())
    synthetixExchanger = interface.IExchanger(zap.synthetixExchanger())
    delegateApprovals = interface.DelegateApprovals("0x15fd6e554874B9e70F832Ed37f231Ac5E142362f")

    delegateApprovals.approveExchangeOnBehalf(zap, {"from": whale})
    sEth.approve(zap, 2 ** 256 - 1, {"from": whale})
    # sETH.approve(whale, 2 ** 256 - 1, {"from": whale})
    sUsd.approve(zap, 2 ** 256 - 1, {"from": whale})

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

    zap.swapEthToSeth({"from": whale, "value": Wei("100 ether")})
    sethBalance = sEth.balanceOf(whale) / Wei("1 ether")
    print(f"sETH actual, 100% swap: {sethBalance} sETH")

    waitLeft = synthetixExchanger.maxSecsLeftInWaitingPeriod(whale.address, sethKey)
    print(f"> Waiting period: {waitLeft} seconds")
    chain.sleep(waitLeft)
    chain.mine(1)

    sethBalance = sEth.balanceOf(whale)
    sEth.approve(whale, sethBalance, {"from": zap})  # this is a bug
    zap.zapIn(sethBalance, {"from": whale})

    yvecrvBalance = vault_ecrv_live.balanceOf(whale) / Wei("1 ether")
    print(f"Vault tokens: {yvecrvBalance} yveCRV")

