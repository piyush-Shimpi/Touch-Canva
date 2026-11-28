#!/usr/bin/env bash
# full part-3 render: frames 1-103 come from the approved hook render
set -u
cd "$(dirname "$0")"
P=/opt/bvenv/bin/python
$P render_shots.py -- hideout.blend 50 16 Cam_S01:1:45:1 Cam_S02:46:103:46 \
  Cam_S03:104:150:104 Cam_S04:151:205:151 Cam_S05:206:262:206 Cam_S06:263:310:263 Cam_S07:311:360:311 \
  Cam_S08:361:404:361 Cam_S09:405:450:405 Cam_S10:451:490:451 Cam_S11:491:540:491 Cam_S12:541:590:541 \
  Cam_S13:591:655:591 Cam_S14:656:712:656 Cam_S15:713:756:713 Cam_S16:757:805:757 Cam_S17:806:855:806
echo ALL RENDERED
