#!/usr/bin/env bash

SLOW_DIR=${SLOW_DIR:-slow}
ROW_COUNT=${ROW_COUNT:-100}

rm -rf ${SLOW_DIR} || exit 1
mkdir -p ${SLOW_DIR} || exit 2
INPUT="$1"
#head -1 ${INPUT} > slow/header.tsv
tail -n +2 ${INPUT} | split -l ${ROW_COUNT} -d - "chunk_"; for file in chunk_*; do mv "$file" "${SLOW_DIR}/$file.tsv"; done
echo "Generated $(ls -l ${SLOW_DIR}/chunk*.tsv | wc -l) files from ${INPUT} with ${ROW_COUNT} rows"

cd ${SLOW_DIR}
#header_file="header.tsv"
table_name="yellow_taxi"

# Ensure pigz is installed
if ! command -v pigz &> /dev/null; then
    echo "Error: pigz is not installed"
    exit 1
fi

# Read the header and convert tabs to commas
#if [[ ! -f "$header_file" ]]; then
#    echo "Error: header.tsv not found!"
#    exit 1
#fi
#header=$(head -n 1 "$header_file" | tr '\t' ',')

# Process all chunk*.tsv files
for data_file in chunk*.tsv; do
    if [[ ! -f "$data_file" ]]; then
        echo "No chunk*.tsv files found."
        exit 1
    fi

    output_file="${data_file%.tsv}.sql"

    # Start SQL INSERT statement
    echo "INSERT INTO $table_name VALUES" > "$output_file"

    # Convert TSV data to SQL VALUES
    awk -F'\t' '
    {
        printf "(NULL,";
        for (i=1; i<=NF; i++) {
            printf "\"%s\"%s", $i, (i==NF ? "" : ", ");
        }
        printf ")%s\n", (NR==100 ? ";" : ",");
    }' "$data_file" >> "$output_file"

    # Ensure the last line ends with a semicolon instead of a comma
    sed -i '$ s/,$/;/' "$output_file"
    echo "SELECT COUNT(*) FROM ${table_name};" >> "$output_file"

    echo "Processed: $data_file -> $output_file"

    # Compress the TSV file using pigz
    pigz "$data_file" &
    echo "Compressed: $data_file.gz"
done

for file in chunk*.sql; do  mysql -ABNs nyc_taxi < $file; done

echo "Processing complete."
