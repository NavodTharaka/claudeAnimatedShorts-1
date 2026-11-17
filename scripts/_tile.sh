#!/bin/bash
# usage: _tile.sh out.jpg in1 in2 ... (hstack at height 960)
out=$1; shift
args=(); fl=""; n=0
for f in "$@"; do args+=(-i "$f"); fl+="[$n:v]scale=-2:960[s$n];"; n=$((n+1)); done
for i in $(seq 0 $((n-1))); do fl+="[s$i]"; done
fl+="hstack=inputs=$n"
ffmpeg -y -loglevel error "${args[@]}" -filter_complex "$fl" -q:v 3 "$out"
