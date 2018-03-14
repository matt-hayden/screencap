
# Do only one file through json_media_info.bash
# This ought to have the same structure as ffprobe

json_media_info.bash "$1" | jq ".[\"$1\"]"

# Persisting output
all_metadata=$(json_media_info.bash "$@")

# Extracting juice

# JSON output
durations=$(jq "with_entries(.value = (.value[\"format\"][\"duration\"] | tonumber))" <<< "$all_metadata")

# text output
duration_of_first=$(jq ".[\"$1\"][\"format\"][\"duration\"] | tonumber" <<< "$all_metadata")
