// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import {Math} from "@openzeppelin/contracts/math/Math.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {SafeERC20, SafeMath, IERC20, Address} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import {ICurveFi} from "../interfaces/curve.sol";
import {IUniswapV2Router02} from "../interfaces/uniswap.sol";
import {IAddressResolver, ISynthetix, IExchanger} from "../interfaces/synthetix.sol";

interface IYVault is IERC20 {
    function deposit(uint256 amount, address recipient) external;

    function withdraw(uint256 shares, address recipient) external;
}

contract ZapYveCRV is Ownable {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public constant uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public constant sushiswapRouter = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;

    IYVault public yVault = IYVault(address(0x0e880118C29F095143dDA28e64d95333A9e75A47));
    ICurveFi public CurveStableSwap = ICurveFi(address(0xc5424B857f758E906013F3555Dad202e4bdB4567)); // Curve ETH/sETH StableSwap pool contract
    IUniswapV2Router02 public swapRouter;
    IAddressResolver public SynthetixResolver = IAddressResolver(address(0x823bE81bbF96BEc0e25CA13170F5AaCb5B79ba83)); // Synthetix AddressResolver contract

    IERC20 public want = IERC20(address(0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c)); // Curve.fi ETH/sETH (eCRV)
    IERC20 public sETH = IERC20(address(0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb)); // Synth sETH
    IERC20 public sUSD = IERC20(address(0x57Ab1ec28D129707052df4dF418D58a2D46d5f51)); // Synth sUSD

    // slippage allowance out of 10000
    uint256 public constant DEFAULT_SLIPPAGE = 50; // 5%
    bool private _noReentry = false;
    address[] public swapPathZapIn;

    constructor() public Ownable() {
        want.safeApprove(address(yVault), uint256(-1));
        want.safeApprove(address(CurveStableSwap), uint256(-1));
        sETH.approve(address(CurveStableSwap), uint256(-1));
        // sUSD.approve(address(Synthetix), uint256(-1));

        swapRouter = IUniswapV2Router02(uniswapRouter);

        swapPathZapIn = new address[](2);
        swapPathZapIn[0] = address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2); //WETH
        swapPathZapIn[1] = address(sUSD);
    }

    // accept ETH
    receive() external payable {
        if (_noReentry) {
            return;
        }
        _zapEthIn(DEFAULT_SLIPPAGE);
    }

    function zapInWithEth(uint256 slippageAllowance) external payable {
        if (_noReentry) {
            return;
        }
        _zapEthIn(slippageAllowance);
    }

    function _zapEthIn(uint256 slippageAllowance) internal {
        uint256 ethBalance = address(this).balance;
        require(ethBalance > 1);

        // Calculate LP tokens from a single-sided ETH deposit
        uint256 expectedLpTokensEth = CurveStableSwap.calc_token_amount([ethBalance, 0], true);

        // Calculate LP tokens from a single-sided sETH deposit
        uint256 expectedSethAmount = _calc_swap_eth_to_seth(ethBalance);
        uint256 expectedLpTokensSeth = CurveStableSwap.calc_token_amount([0, expectedSethAmount], true);

        // Calculate LP tokens from a balanced deposit
        uint256 halfEthBalance = ethBalance.div(2);
        expectedSethAmount = _calc_swap_eth_to_seth(halfEthBalance);
        uint256 expectedLpTokensBalanced = CurveStableSwap.calc_token_amount([halfEthBalance, expectedSethAmount], true);

        if (expectedLpTokensSeth > expectedLpTokensEth && expectedLpTokensSeth > expectedLpTokensBalanced) {
            _swap_eth_to_seth(ethBalance);
        } else if (expectedLpTokensBalanced > expectedLpTokensEth && expectedLpTokensBalanced > expectedLpTokensSeth) {
            _swap_eth_to_seth(halfEthBalance);
        }

        uint256 startingEthBalance = ethBalance;
        ethBalance = address(this).balance;
        uint256 sethBalance = sETH.balanceOf(address(this));
        CurveStableSwap.add_liquidity{value: ethBalance}([ethBalance, sethBalance], 0);

        uint256 outAmount = want.balanceOf(address(this));
        require(outAmount.mul(slippageAllowance.add(10000)).div(10000) >= startingEthBalance, "TOO MUCH SLIPPAGE");

        yVault.deposit(outAmount, msg.sender);
    }

    function _calc_swap_eth_to_seth(uint256 ethAmount) internal returns (uint256 expectedSethAmount) {
        IExchanger synthetixExchanger = IExchanger(SynthetixResolver.getAddress("Exchanger"));
        require(address(synthetixExchanger) != address(0), "Exchanger is missing from Synthetix resolver");

        uint256[] memory amounts = IUniswapV2Router02(swapRouter).getAmountsOut(ethAmount, swapPathZapIn);
        uint256 expectedSusdAmount = amounts[amounts.length - 1];
        (expectedSethAmount, , ) = synthetixExchanger.getAmountsForExchange(expectedSusdAmount, "sUSD", "sETH");
    }

    function _swap_eth_to_seth(uint256 ethAmount) internal {
        ISynthetix synthetix = ISynthetix(SynthetixResolver.getAddress("Synthetix"));
        require(address(synthetix) != address(0), "Synthetix is missing from Synthetix resolver");

        IUniswapV2Router02(swapRouter).swapExactETHForTokens{value: ethAmount}(ethAmount, swapPathZapIn, address(this), now);
        uint256 susdAmount = sUSD.balanceOf(address(this));
        synthetix.exchange("sUSD", susdAmount, "sETH");
    }

    function zapOutToEth(uint256 lpTokenAmount, uint256 slippageAllowance) external {
        _zapOut(lpTokenAmount, slippageAllowance);
    }

    function _zapOut(uint256 lpTokenAmount, uint256 slippageAllowance) internal {
        require(yVault.balanceOf(msg.sender) >= lpTokenAmount, "NOT ENOUGH BALANCE");
        yVault.withdraw(lpTokenAmount, address(this));

        uint256 balance = want.balanceOf(address(this));
        require(balance > 0, "no balance");

        // // Calculate single-sided ETH withdrawl
        // uint256 expectedEth = CurveStableSwap.calc_withdraw_one_coin(balance, 0);

        // // Calculate LP tokens from a single-sided sETH deposit
        // uint256 expectedSethAmount = _calc_swap_eth_to_seth(ethBalance);
        // uint256 expectedLpTokensSeth = CurveStableSwap.calc_token_amount([0, expectedSethAmount], true);

        // // Calculate LP tokens from a balanced deposit
        // uint256 halfEthBalance = ethBalance.div(2);
        // expectedSethAmount = _calc_swap_eth_to_seth(halfEthBalance);
        // uint256 expectedLpTokensBalanced = CurveStableSwap.calc_token_amount([halfEthBalance, expectedSethAmount], true);

        // if (expectedLpTokensSeth > expectedLpTokensEth && expectedLpTokensSeth > expectedLpTokensBalanced) {
        //     _swap_eth_to_seth(ethBalance);
        // } else if (expectedLpTokensBalanced > expectedLpTokensEth && expectedLpTokensBalanced > expectedLpTokensSeth) {
        //     _swap_eth_to_seth(halfEthBalance);
        // }

        // _noReentry = true;
        // CurveStableSwap.remove_liquidity_one_coin(balance, zero_if_eth, 0);
        // _noReentry = false;

        uint256 endBalance;
        endBalance = address(this).balance;
        msg.sender.transfer(endBalance);

        require(endBalance.mul(slippageAllowance.add(10000)).div(10000) >= balance, "TOO MUCH SLIPPAGE");
    }

    //There should never be any tokens in this contract
    function rescueTokens(address token, uint256 amount) external onlyOwner {
        if (token == address(0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE)) {
            amount = Math.min(address(this).balance, amount);
            msg.sender.transfer(amount);
        } else {
            IERC20 want = IERC20(token);
            amount = Math.min(want.balanceOf(address(this)), amount);
            want.safeTransfer(msg.sender, amount);
        }
    }

    function updateVaultAddress(address _vault) external onlyOwner {
        yVault = IYVault(_vault);
        want.safeApprove(_vault, uint256(-1));
    }

    function setSwapRouter(bool isUniswap, address[] calldata _swapPathZapIn) public onlyOwner {
        if (isUniswap) {
            swapRouter = IUniswapV2Router02(uniswapRouter);
        } else {
            swapRouter = IUniswapV2Router02(sushiswapRouter);
        }
        swapPathZapIn = _swapPathZapIn;
        //  WETH.approve(swapRouter, uint256(-1));
    }
}
