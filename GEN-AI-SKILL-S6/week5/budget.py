import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class FeatureBudget:

    requests_per_day: int
    avg_input_tokens: int
    avg_output_tokens: int
    peak_requests_per_minute: int

    input_price_per_million: float
    output_price_per_million: float

    rpm_limit: int
    tpm_limit: int

    monthly_budget_usd: float
    daily_budget_usd: float

    safety_margin_percent: float

    @classmethod
    def from_env(cls):
        return cls(
            requests_per_day=int(os.getenv("REQUESTS_PER_DAY", "0")),
            avg_input_tokens=int(os.getenv("AVG_INPUT_TOKENS", "0")),
            avg_output_tokens=int(os.getenv("AVG_OUTPUT_TOKENS", "0")),
            peak_requests_per_minute=int(os.getenv("PEAK_REQUESTS_PER_MINUTE", "0")),

            input_price_per_million=float(os.getenv("INPUT_PRICE_PER_MILLION", "0")),
            output_price_per_million=float(os.getenv("OUTPUT_PRICE_PER_MILLION", "0")),

            rpm_limit=int(os.getenv("RPM_LIMIT", "0")),
            tpm_limit=int(os.getenv("TPM_LIMIT", "0")),

            monthly_budget_usd=float(os.getenv("MONTHLY_BUDGET_USD", "0")),
            daily_budget_usd=float(os.getenv("DAILY_BUDGET_USD", "0")),

            safety_margin_percent=float(os.getenv("SAFETY_MARGIN_PERCENT", "20"))
        )

    def calculate(self):

        if min(
            self.requests_per_day,
            self.avg_input_tokens,
            self.avg_output_tokens,
            self.peak_requests_per_minute
        ) < 0:
            raise ValueError("Usage assumptions cannot be negative.")

        if self.safety_margin_percent < 0:
            raise ValueError("Safety margin cannot be negative.")

        # Calculate daily token consumption
        input_day = self.requests_per_day * self.avg_input_tokens

        output_day = self.requests_per_day * self.avg_output_tokens

        # Calculate API cost
        daily_cost = (
            input_day * self.input_price_per_million
            + output_day * self.output_price_per_million
        ) / 1_000_000

        monthly_cost = daily_cost * 30

        # Apply safety margin
        margin = 1 + self.safety_margin_percent / 100

        # Calculate peak capacity requirements
        peak_rpm = self.peak_requests_per_minute * margin

        peak_tpm = (
            self.peak_requests_per_minute
            * (self.avg_input_tokens + self.avg_output_tokens)
            * margin
        )

        return {
            "input_tokens_day": input_day,
            "output_tokens_day": output_day,
            "total_tokens_day": input_day + output_day,

            "daily_cost_usd": daily_cost,
            "monthly_cost_usd": monthly_cost,

            "peak_rpm_with_margin": peak_rpm,
            "peak_tpm_with_margin": peak_tpm,

            "rpm_ok": peak_rpm <= self.rpm_limit,
            "tpm_ok": peak_tpm <= self.tpm_limit,

            "daily_budget_ok": daily_cost * margin <= self.daily_budget_usd,
            "monthly_budget_ok": monthly_cost * margin <= self.monthly_budget_usd
        }


def main():

    budget = FeatureBudget.from_env()

    result = budget.calculate()

    print("\nTOKEN ECONOMICS REPORT")
    print("-" * 35)

    print(f"Input tokens/day: {result['input_tokens_day']:,.0f}")
    print(f"Output tokens/day: {result['output_tokens_day']:,.0f}")
    print(f"Total tokens/day: {result['total_tokens_day']:,.0f}")

    print(f"Estimated daily cost: ${result['daily_cost_usd']:.4f}")
    print(f"Estimated monthly cost: ${result['monthly_cost_usd']:.2f}")

    print(f"Peak RPM with margin: {result['peak_rpm_with_margin']:.1f}")
    print(f"Peak TPM with margin: {result['peak_tpm_with_margin']:.0f}")

    checks = {
        "RPM capacity": result["rpm_ok"],
        "TPM capacity": result["tpm_ok"],
        "Daily budget": result["daily_budget_ok"],
        "Monthly budget": result["monthly_budget_ok"]
    }

    print("\nCHECKS")

    for name, passed in checks.items():
        print(f"{name}: {'PASS' if passed else 'REVIEW'}")

    if all(checks.values()):
        print("\nRecommendation: WITHIN configured planning limits.")
    else:
        print("\nRecommendation: REVISE assumptions, limits, or design before build.")


if __name__ == "__main__":
    main()