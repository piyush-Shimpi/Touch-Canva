#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
P=/opt/bvenv/bin/python
$P render_shots.py -- map.blend 50 16 Cam_S04:61:63:154 Cam_S04b:104:144:197
EXPOSURE=0.7 $P render_shots.py -- city.blend 50 24 Cam_S07:310:342:325
EXPOSURE=0.6 $P render_shots.py -- road.blend 50 24 Cam_S09:1:48:403
$P render_shots.py -- mountain.blend 50 24 Cam_S11:1:33:499
echo FIX RENDERED
