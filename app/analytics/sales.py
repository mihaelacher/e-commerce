import pandas as pd


def best_selling_products(data, limit: int) -> list[dict]:
    df = pd.DataFrame(data)

    if df.empty:
        return []
    
    return (
        df
        .groupby(["product_id", "product_name"], as_index=False)
        .agg(
            units_sold=("quantity", "sum"),
            revenue=("total_price", "sum"),
        )
        .sort_values(
            ["units_sold", "revenue", "product_id"],
            ascending=[False, False, True],
        )
        .head(limit)
        .to_dict(orient="records")
    )


def daily_sales(data) -> list[dict]:
    df = pd.DataFrame(data)

    if df.empty:
        return []

    df["date"] = (
        pd.to_datetime(df["created_at"], utc=True)
        .dt.tz_convert("Europe/Sofia")
        .dt.date
    )

    return (
        df
        .groupby("date", as_index=False)
        .agg(
            orders=("order_id", "nunique"),
            units_sold=("quantity", "sum"),
            revenue=("total_price", "sum"),
        )
        .sort_values("date")
        .to_dict(orient="records")
    )