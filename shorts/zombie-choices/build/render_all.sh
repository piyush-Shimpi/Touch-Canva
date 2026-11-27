#!/usr/bin/env bash
# part 2 full render: 660 frames (1-75 come from the approved hook test)
set -u
cd "$(dirname "$0")"
P=/opt/bvenv/bin/python
$P render_shots.py -- house.blend 50 16 Cam_S01:1:39:1 Cam_S02:40:75:40 Cam_S03:200:242:76 Cam_S04:260:309:119 Cam_S05:320:367:169 Cam_S06:380:421:217 Cam_S10:440:484:388 Cam_S11:500:541:433 Cam_S12:560:601:475 Cam_S01:-41:0:619
$P render_shots.py -- yard.blend 50 16 Cam_S07:1:42:259 Cam_S08:118:153:301 Cam_S09:110:160:337
$P render_shots.py -- escape.blend 50 16 Cam_S13:1:48:517 Cam_S14:5:58:565
echo ALL RENDERED
