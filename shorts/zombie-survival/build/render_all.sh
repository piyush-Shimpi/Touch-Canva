#!/usr/bin/env bash
# full zombie short: 660 frames (hook frames 1-93 come from the approved hook render)
set -u
cd "$(dirname "$0")"
P=/opt/bvenv/bin/python
$P render_shots.py -- map.blend 50 16 Cam_S03:1:63:94 Cam_S04:64:144:157 Cam_S10:200:247:451 Cam_S12:300:344:532
$P render_shots.py -- city.blend 50 24 Cam_S01:1:93:1 Cam_S05:200:247:238 Cam_S06:260:298:286 Cam_S07:310:342:325 Cam_S01:-32:0:628
$P render_shots.py -- pack.blend 50 28 Cam_S08:1:45:358
$P render_shots.py -- road.blend 50 24 Cam_S09:1:48:403
$P render_shots.py -- mountain.blend 50 24 Cam_S11:1:33:499 Cam_S13:60:83:577 Cam_S14:100:126:601
echo ALL RENDERED
