import pandas as pd
from geonormpy.norms.batch import calculate_cipw_dataframe


def process_batch(input_file, output_file):
    df = pd.read_csv(input_file)

    oxide_cols = [
        "SiO2",
        "TiO2",
        "Al2O3",
        "Fe2O3",
        "FeO",
        "FeOT",
        "MnO",
        "MgO",
        "CaO",
        "Na2O",
        "K2O",
        "P2O5",
        "ZrO2",
        "Cr2O3",
        "CO2",
        "S",
        "F",
        "Cl",
        "SO3",
    ]
    use_cols = [col for col in oxide_cols if col in df.columns]

    results_df = calculate_cipw_dataframe(df[use_cols])

    if "Sample_ID" in df.columns:
        results_df.insert(0, "Sample_ID", df["Sample_ID"])

    if "Notes" in df.columns:
        results_df.insert(1, "Notes", df["Notes"])

    results_df.to_csv(output_file, index=False)

    print(
        f"Processing complete. Generated {len(results_df.columns)} columns in: {output_file}"
    )


if __name__ == "__main__":
    process_batch("data/test_data.csv", "data/normative_results.csv")