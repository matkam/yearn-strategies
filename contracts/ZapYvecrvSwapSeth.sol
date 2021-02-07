// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import {Math} from "@openzeppelin/contracts/math/Math.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {SafeERC20, SafeMath, IERC20, Address} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";

import {ICurveFi} from "../interfaces/curve.sol";
import {IUniswapV2Router02} from "../interfaces/uniswap.sol";

interface IYVault is IERC20 {
    function deposit(uint256 amount, address recipient) external;

    function withdraw() external;

    function pricePerShare() external view returns (uint256);
}

contract ZapYvecrvSwapSeth is Ownable {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public constant uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address public constant sushiswapRouter = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;

    IYVault public yVault = IYVault(address(0x0e880118C29F095143dDA28e64d95333A9e75A47));
    ICurveFi public CurveStableSwap = ICurveFi(address(0xc5424B857f758E906013F3555Dad202e4bdB4567)); // Curve ETH/sETH StableSwap pool contract
    IUniswapV2Router02 public SwapRouter;

    IERC20 public want = IERC20(address(0xA3D87FffcE63B53E0d54fAa1cc983B7eB0b74A9c)); // Curve.fi ETH/sETH (eCRV)
    IERC20 public WETH = IERC20(address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2));
    IERC20 public sETH = IERC20(address(0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb)); // Synthetix ProxysETH

    uint256 public constant DEFAULT_SLIPPAGE = 200; // slippage allowance out of 10000: 2%
    bool private _noReentry = false;
    address[] public swapPathZapIn;
    address[] public swapPathZapOut;

    constructor() public Ownable() {
        SwapRouter = IUniswapV2Router02(uniswapRouter);

        swapPathZapIn = new address[](2);
        swapPathZapIn[0] = address(WETH);
        swapPathZapIn[1] = address(sETH);

        // In approves
        sETH.approve(address(CurveStableSwap), uint256(-1));
        want.safeApprove(address(yVault), uint256(-1));

        // Out approves
        want.safeApprove(address(CurveStableSwap), uint256(-1));
    }

    // Accept ETH and zap in with no token swap
    receive() external payable {
        if (_noReentry) {
            return;
        }
        _zapIn(0);
    }

    //
    // Zap In
    //

    function zapIn(uint256 slippageAllowance) external payable {
        if (_noReentry) {
            return;
        }
        if (slippageAllowance == 0) {
            slippageAllowance = DEFAULT_SLIPPAGE;
        }
        _zapIn(slippageAllowance);
    }

    function _zapIn(uint256 slippageAllowance) internal {
        uint256 ethDeposit = address(this).balance;
        require(ethDeposit > 1, "INSUFFICIENT ETH DEPOSIT");

        (uint256 oneSidedWantAmount, ) = estimateZapIn(ethDeposit, 0);
        (uint256 halfSwapWantAmount, uint256 halfSwapEthAmountSwap) = estimateZapIn(ethDeposit, 50);
        (uint256 fullSwapWantAmount, uint256 fullSwapEthAmountSwap) = estimateZapIn(ethDeposit, 100);

        if (fullSwapWantAmount > oneSidedWantAmount && fullSwapWantAmount > halfSwapWantAmount) {
            SwapRouter.swapExactETHForTokens{value: halfSwapEthAmountSwap}(0, swapPathZapIn, address(this), now);
        } else if (halfSwapWantAmount > oneSidedWantAmount && halfSwapWantAmount > fullSwapWantAmount) {
            SwapRouter.swapExactETHForTokens{value: fullSwapEthAmountSwap}(0, swapPathZapIn, address(this), now);
        }

        uint256 ethBalance = address(this).balance;
        uint256 sethBalance = sETH.balanceOf(address(this));
        CurveStableSwap.add_liquidity{value: ethBalance}([ethBalance, sethBalance], 0);

        uint256 outAmount = want.balanceOf(address(this));
        require(outAmount.mul(slippageAllowance.add(10000)).div(10000) >= ethDeposit, "TOO MUCH SLIPPAGE");

        yVault.deposit(outAmount, msg.sender);
    }

    function estimateZapIn(uint256 ethDeposit, uint256 percentSwap) public view returns (uint256 estimatedWant, uint256 ethAmountForSwap) {
        require(percentSwap >= 0 && percentSwap <= 100, "INVALID PERCENTAGE VALUE");

        uint256 estimatedSethAmount = 0;
        if (percentSwap > 0) {
            ethAmountForSwap = ethDeposit.mul(percentSwap).div(100);
            ethDeposit = ethDeposit.sub(ethAmountForSwap);

            uint256[] memory amounts = SwapRouter.getAmountsOut(ethAmountForSwap, swapPathZapIn);
            estimatedSethAmount = amounts[amounts.length - 1];
        }

        estimatedWant = CurveStableSwap.calc_token_amount([ethDeposit, estimatedSethAmount], true);
    }

    //
    // Zap Out
    //

    function zapOut(uint256 yvTokenAmount, uint256 slippageAllowance) external {
        uint256 yvTokenWithdrawl = Math.min(yvTokenAmount, yVault.balanceOf(msg.sender));
        require(yvTokenWithdrawl > 0, "INSUFFICIENT FUNDS");

        yVault.transferFrom(msg.sender, address(this), yvTokenWithdrawl);
        yVault.withdraw();
        uint256 wantBalance = want.balanceOf(address(this));

        _noReentry = true;
        CurveStableSwap.remove_liquidity_one_coin(wantBalance, 0, 0);
        _noReentry = false;

        uint256 ethBalance = address(this).balance;
        msg.sender.transfer(ethBalance);

        require(ethBalance.mul(slippageAllowance.add(10000)).div(10000) >= wantBalance, "TOO MUCH SLIPPAGE");

        uint256 leftover = yVault.balanceOf(address(this));
        if (leftover > 0) {
            yVault.transfer(msg.sender, leftover);
        }
    }

    //
    // Misc external functions
    //

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

    function setSwapRouter(bool isUniswap, address[] calldata _swapPathZapIn) external onlyOwner {
        if (isUniswap) {
            SwapRouter = IUniswapV2Router02(uniswapRouter);
        } else {
            SwapRouter = IUniswapV2Router02(sushiswapRouter);
        }

        swapPathZapIn = _swapPathZapIn;
    }
}
