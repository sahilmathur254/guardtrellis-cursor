#!/bin/sh
# Local invocation only. Setup and all dependency downloads are explicit Terminal tasks.
set -u

gt_cursor_mode=${1-}
gt_cursor_profile=advisory

gt_cursor_unavailable() {
    gt_cursor_reason=$1
    printf '%s\n' '{"component":"guardtrellis_cursor_launcher","check_status":"unavailable","reason_code":"'"$gt_cursor_reason"'"}' >&2
    if [ "$gt_cursor_mode" = hook ]; then
        if [ "$gt_cursor_profile" = advisory ]; then
            printf '%s\n' '{"continue":true}'
        else
            printf '%s\n' '{"continue":false,"user_message":"GuardTrellis could not check this prompt. This configured check requests cancellation."}'
        fi
        exit 0
    fi
    exit 1
}

if [ "$#" -gt 0 ]; then
    shift
fi
case "$gt_cursor_mode" in
    hook)
        if [ "$#" -eq 2 ] && [ "$1" = --profile ]; then
            case "$2" in
                advisory|enforce-secrets-v1) gt_cursor_profile=$2 ;;
                *) gt_cursor_profile=invalid; gt_cursor_unavailable invalid_configuration ;;
            esac
        elif [ "$#" -ne 0 ]; then
            gt_cursor_profile=invalid
            gt_cursor_unavailable invalid_configuration
        fi
        ;;
    prepare)
        if [ "$#" -eq 0 ]; then
            :
        elif [ "$#" -eq 7 ] && [ "$1" = --open ] &&
             [ "$2" = --user-data-dir ] && [ "$4" = --extensions-dir ] &&
             [ "$6" = --cursor-profile ]; then
            :
        else
            gt_cursor_unavailable invalid_configuration
        fi
        ;;
    *) gt_cursor_unavailable invalid_configuration ;;
esac

if [ "$(/usr/bin/uname -s 2>/dev/null)" != Darwin ]; then
    gt_cursor_unavailable unsupported_platform
fi
gt_cursor_script_dir=$(/usr/bin/dirname "$0")
gt_cursor_root=$(CDPATH= cd "$gt_cursor_script_dir/.." 2>/dev/null && pwd -P 2>/dev/null) || gt_cursor_unavailable runtime_unavailable

if [ "${GUARDTRELLIS_CURSOR_RUNTIME+x}" = x ]; then
    gt_cursor_runtime=$GUARDTRELLIS_CURSOR_RUNTIME
else
    case "${HOME-}" in
        /*) gt_cursor_runtime="$HOME/Library/Application Support/GuardTrellis/Cursor/0.1.0-preview.1-sdk0.1.9" ;;
        *) gt_cursor_unavailable runtime_unavailable ;;
    esac
fi
case "$gt_cursor_runtime" in
    /*) ;;
    *) gt_cursor_unavailable runtime_unavailable ;;
esac
gt_cursor_runtime_real=$(CDPATH= cd "$gt_cursor_runtime" 2>/dev/null && pwd -P 2>/dev/null) || gt_cursor_unavailable runtime_unavailable
case "$gt_cursor_runtime_real" in
    "$gt_cursor_root"|"$gt_cursor_root"/*) gt_cursor_unavailable runtime_unavailable ;;
esac

# A setup-completion marker is not a source or interpreter authenticity guarantee.
gt_cursor_marker="$gt_cursor_runtime_real/.guardtrellis-cursor-runtime-v1"
gt_cursor_tag=0.1.0-preview.1-sdk0.1.9
if [ ! -f "$gt_cursor_marker" ] || [ -L "$gt_cursor_marker" ]; then
    gt_cursor_unavailable runtime_unavailable
fi
gt_cursor_marker_size=$(/usr/bin/wc -c 2>/dev/null < "$gt_cursor_marker") || gt_cursor_unavailable runtime_unavailable
if [ "$gt_cursor_marker_size" -ne "${#gt_cursor_tag}" ] && [ "$gt_cursor_marker_size" -ne "$(( ${#gt_cursor_tag} + 1 ))" ]; then
    gt_cursor_unavailable runtime_unavailable
fi
if printf '%s' "$gt_cursor_tag" | /usr/bin/cmp -s "$gt_cursor_marker" -; then
    :
elif printf '%s\n' "$gt_cursor_tag" | /usr/bin/cmp -s "$gt_cursor_marker" -; then
    :
else
    gt_cursor_unavailable runtime_unavailable
fi
gt_cursor_python="$gt_cursor_runtime_real/bin/python"
if [ ! -f "$gt_cursor_python" ] || [ ! -x "$gt_cursor_python" ]; then
    gt_cursor_unavailable runtime_unavailable
fi

if [ "$gt_cursor_mode" = hook ]; then
    gt_cursor_script="$gt_cursor_root/adapters/cursor/prompt_check.py"
    if [ ! -f "$gt_cursor_script" ] || [ -L "$gt_cursor_script" ]; then
        gt_cursor_unavailable runtime_unavailable
    fi
    exec "$gt_cursor_python" -I -B "$gt_cursor_script" --profile "$gt_cursor_profile" --diagnostics findings
fi
gt_cursor_script="$gt_cursor_root/adapters/cursor/prepare_prompt.py"
if [ ! -f "$gt_cursor_script" ] || [ -L "$gt_cursor_script" ]; then
    gt_cursor_unavailable runtime_unavailable
fi
exec "$gt_cursor_python" -I -B "$gt_cursor_script" "$@"
