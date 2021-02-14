// SPDX-License-Identifier: AGPL-3.0
pragma solidity 0.6.12;
pragma experimental ABIEncoderV2;

import {BaseStrategy} from "@yearnvaults/contracts/BaseStrategy.sol";
import {SafeERC20, SafeMath, IERC20, Address} from "@openzeppelin/contracts/token/ERC20/SafeERC20.sol";
import {Math} from "@openzeppelin/contracts/math/Math.sol";

import {ICurveFi, ICrvV3} from "../interfaces/curve.sol";
import {IUniswapV2Router02} from "../interfaces/uniswap.sol";
import {StrategyProxy} from "../interfaces/yearn.sol";

contract StrategyCurveEcrv is BaseStrategy {
    using SafeERC20 for IERC20;
    using Address for address;
    using SafeMath for uint256;

    address public constant gauge = address(0x3C0FFFF15EA30C35d7A85B85c0782D6c94e1d238);

    address private uniswapRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address private sushiswapRouter = 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F;

    address public crvRouter = 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D;
    address[] public crvPathWeth;

    ICurveFi public curveStableSwap = ICurveFi(address(0xc5424B857f758E906013F3555Dad202e4bdB4567)); // Curve ETH/sETH StableSwap pool contract
    StrategyProxy public proxy = StrategyProxy(address(0x9a3a03C614dc467ACC3e81275468e033c98d960E));

    IERC20 public weth = IERC20(address(0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2));
    IERC20 public sEth = IERC20(address(0x5e74C9036fb86BD7eCdcb084a0673EFc32eA31cb));
    ICrvV3 public crv = ICrvV3(address(0xD533a949740bb3306d119CC777fa900bA034cd52));

    constructor(address _vault) public BaseStrategy(_vault) {
        want.safeApprove(address(proxy), uint256(-1));
        crv.approve(crvRouter, uint256(-1));

        crvPathWeth = new address[](2);
        crvPathWeth[0] = address(crv);
        crvPathWeth[1] = address(weth);
    }

    function name() external view override returns (string memory) {
        return "StrategyCurveEcrvStrategyProxy";
    }

    function estimatedTotalAssets() public view override returns (uint256) {
        return proxy.balanceOf(gauge);
    }

    function prepareReturn(uint256 _debtOutstanding)
        internal
        override
        returns (
            uint256 _profit,
            uint256 _loss,
            uint256 _debtPayment
        )
    {
        // TODO: Do stuff here to free up any returns back into `want`
        // NOTE: Return `_profit` which is value generated by all positions, priced in `want`
        // NOTE: Should try to free up at least `_debtOutstanding` of underlying position

        uint256 gaugeTokens = proxy.balanceOf(gauge);
        if (gaugeTokens > 0) {
            proxy.harvest(gauge);

            uint256 crvBalance = crv.balanceOf(address(this));
            if (crvBalance > 0) {
                IUniswapV2Router02(crvRouter).swapExactTokensForETH(crvBalance, uint256(0), crvPathWeth, address(this), now);
            }

            uint256 ethBalance = address(this).balance;
            if (ethBalance > 0) {
                curveStableSwap.add_liquidity{value: ethBalance}([ethBalance, 0], 0);
            }

            _profit = want.balanceOf(address(this));
        }

        if (_debtOutstanding > 0) {
            if (_debtOutstanding > _profit) {
                uint256 stakedBal = proxy.balanceOf(gauge);
                proxy.withdraw(gauge, address(want), Math.min(stakedBal, _debtOutstanding - _profit));
            }

            _debtPayment = Math.min(_debtOutstanding, want.balanceOf(address(this)).sub(_profit));
        }
    }

    function adjustPosition(uint256 _debtOutstanding) internal override {
        uint256 _toInvest = want.balanceOf(address(this));
        want.safeTransfer(address(proxy), _toInvest);
        proxy.deposit(gauge, address(want));
    }

    function liquidatePosition(uint256 _amountNeeded) internal override returns (uint256 _liquidatedAmount, uint256 _loss) {
        uint256 wantBal = want.balanceOf(address(this));
        uint256 stakedBal = proxy.balanceOf(gauge);

        if (_amountNeeded > wantBal) {
            proxy.withdraw(gauge, address(want), Math.min(stakedBal, _amountNeeded - wantBal));
        }

        _liquidatedAmount = Math.min(_amountNeeded, want.balanceOf(address(this)));
    }

    // NOTE: Can override `tendTrigger` and `harvestTrigger` if necessary

    function prepareMigration(address _newStrategy) internal override {
        // TODO: Transfer any non-`want` tokens to the new strategy
        // NOTE: `migrate` will automatically forward all `want` in this strategy to the new one
        prepareReturn(proxy.balanceOf(gauge));
    }

    function protectedTokens() internal view override returns (address[] memory) {
        address[] memory protected = new address[](1);
        protected[0] = gauge;

        return protected;
    }

    //
    // helper functions
    //
    function setCRVRouter(bool isUniswap, address[] calldata _wethPath) public onlyGovernance {
        if (isUniswap) {
            crvRouter = uniswapRouter;
        } else {
            crvRouter = sushiswapRouter;
        }
        crvPathWeth = _wethPath;
        crv.approve(crvRouter, uint256(-1));
    }

    function setProxy(address _proxy) public onlyGovernance {
        proxy = StrategyProxy(_proxy);
    }

    // enable ability to recieve ETH
    receive() external payable {}
}
