# OpenAlex Silver-labelled Thesis Topic Dataset

This folder contains a reproducible silver-labelled dataset for thesis topic
novelty assessment and duplicate detection.

## Source choice

OpenAlex was used because it provides a stable public API, structured metadata,
dissertation filtering, titles, abstracts when available, publication years,
language metadata, and topic/concept metadata. NDLTD and OATD are highly relevant
for thesis records, but they are less convenient for reproducible automated
collection in this prototype.

## Files

- `openalex_thesis_topics.csv`: topic records derived from OpenAlex dissertation metadata.
- `openalex_labelled_pairs.csv`: silver-labelled topic pairs.
- `raw/`: raw OpenAlex API responses used to build the dataset.

## Dataset size

- Total topic records: 230
- Real OpenAlex records: 160
- Controlled synthetic variants: 70
- Total labelled pairs: 130
- Duplicate pairs: 30
- Near-duplicate pairs: 40
- Novel pairs: 60

## Important limitation

The labels are silver labels, not expert human labels. Duplicate and
near-duplicate examples are controlled variants derived from real OpenAlex
dissertation records. Novel examples are pairs from different OpenAlex domains
with low lexical overlap. This dataset is appropriate for prototype validation,
threshold tuning, and methodology demonstration. For a final dissertation or
publication, a subset should be manually reviewed by domain experts.

## Recommended usage

Use this dataset as an intermediate benchmark before collecting real university
thesis topics. Report results as preliminary and clearly state the labelling
strategy.
