# Zombie series, part 2: "What would YOU do?" (plan pack v1, awaiting OK)

**Premise:** Zombies are at your door. You pick: stay home, dig a bunker, or… Each wrong choice fails fast, with real numbers.
**Length:** 22.0 s (11 bars @ 120 BPM, loops) · 1080x1920 · 30 fps
**Tools:** Blender 5.3 (bpy) + your mixamo-library · voice Kokoro am_michael · synthesised music

## A. Script (55 words, loops mid-sentence)
| # | Line | ≈ time |
|---|---|---|
| 1 | "Zombies outside your door. What do you do?" | 0.0–2.6 |
| 2 | "Stay home? Most homes have food for about three days." | 2.7–5.6 |
| 3 | "After three weeks without food, you're too weak to run." | 5.7–8.6 |
| 4 | "Dig a bunker? Hard soil takes about a day per cubic meter." | 8.7–12.0 |
| 5 | "Too slow." | 12.1–12.9 |
| 6 | "Real answer: water first. Three days without it, and you're done." | 13.0–16.8 |
| 7 | (music + action beat, no voice) | 16.8–20.6 |
| 8 | "So the second you hear…" → loops into line 1 | 20.6–22.0 |

Loop read-aloud: *"So the second you hear — zombies outside your door. What do you do?"*

## B. Shot list (15 shots)
```
S01 · 0.0–1.3 · CU door, low angle · handheld shake
  What: front door bursting inward on its chain, a zombie arm punches through the gap
  Sound: "Zombies outside your door…" · SFX: door BANG on frame 0 + wood crack
  Text: label "YOUR MOVE?"
S02 · 1.3–2.6 · MCU Remy · push-in
  What: Remy backs away from the door, looks left/right (deciding)
  Text: HUD "STAY · DIG · ?"
S03 · 2.6–4.0 · MEDIUM kitchen · whip pan in
  What: CHOICE A: Remy shoves the fridge against the door (barricade)
  Text: caption "STAY HOME?"
S04 · 4.0–5.6 · ECU fridge · time-lapse
  What: fridge shelves empty one by one, food vanishing
  Text: HUD "~3 DAYS"
S05 · 5.6–7.2 · WIDE kitchen, top-down · slow push
  What: Remy slumped on the floor, weak; day counter racing to "DAY 21"; zombie shadows at the window
S06 · 7.2–8.6 · CU · freeze + red ✗ stamp (hit-frame)
  What: "✗" stamps over the kitchen; whoosh to the backyard
S07 · 8.6–10.0 · MEDIUM backyard · tracking
  What: CHOICE B: Remy digging hard with a shovel, golden hour
  Text: caption "DIG A BUNKER?"
S08 · 10.0–11.2 · ECU shovel blade · low
  What: blade clanks on hard dirt, barely a scoop
  Text: HUD "1 M³ ≈ 1 DAY (est.)"
S09 · 11.2–12.9 · TOP-DOWN crane up
  What: tiny hole… zombies already climbing the backyard fence. "✗"
S10 · 12.9–14.4 · CRASH ZOOM · ECU
  What: a gallon water jug slams onto the counter
  Text: caption "WATER FIRST" (key: WATER)
S11 · 14.4–15.8 · MCU · push-in
  What: Remy fills jugs at the sink / bathtub, fast cuts
  Text: HUD "3 DAYS WITHOUT IT"
S12 · 15.8–17.2 · PEAK · wide, low angle · hit-frame + white flash
  What: the door finally bursts open; Remy is already out the back with the water pack
S13 · 17.2–18.8 · tracking · golden-hour street
  What: Remy runs off with the orange backpack; horde behind (callback to part 1)
S14 · 18.8–20.6 · CU · look back
  What: he looks back at his house full of zombies, breathing hard
S15 · 20.6–22.0 · WHIP PAN → match cut to frame 0 (the door bursting)
  Sound: "So the second you hear…" → loop
```
**ON-SCREEN WORDS:** YOUR MOVE · STAY · DIG · STAY HOME · ~3 DAYS · DAY 21 · DIG A BUNKER · 1 M³ ≈ 1 DAY (EST.) · WATER FIRST · 3 DAYS WITHOUT IT, plus narration captions.

## C. Loop
Line 8 runs straight into line 1 with no pause. The music is 11 bars at 120 BPM. S15 ends on S01's first frame.

## D. Characters
- **Remy** again (same hero = series continuity), orange backpack in the escape.
- Zombies: War Zombie / Cop Zombie / Zombie Girl, recoloured with no gore.

## E. Real-world demo
Each choice gets a **visible clock**: the fridge emptying with a day counter, a shovel against a dirt counter, a water jug against "3 DAYS". Wrong choices end with a red ✗ stamp.

## F. Sound
- **Frame 0:** door BANG with a wood crack.
- **Kitchen:** clock-tick time-lapse.
- **Digging:** shovel clanks.
- **Peak:** door burst with an impact and the music dropping out first.
- **Escape:** whoosh into the loop.
- **Music:** tense pulse at 120 BPM, ducked under the voice.

## G. Honesty note
- Mixamo faces don't move. Weakness, fear and effort come from body poses.
- The house interior is built in 3D from simple pieces plus CC0 textures, stylised rather than photoreal.
- "About 3 days of food" comes from a Census survey (82% of households have 3 days of non-perishable food). It's a typical figure, not an exact one.
- "3 weeks / 3 days" is the survival **rule of threes**, a rough guide rather than a hard limit. The script says "about" and "too weak".
- The digging speed is a **rough estimate** (hard soil: about a day per cubic metre by hand) and is labelled "est." on screen.
- Rendering takes about 2 hours.

## H. What I need from Mixamo (FBX Binary, **Without Skin**, 30 fps)
1. **Digging**: search "digging" or "shoveling". This is the key one for choice B.
2. **Sitting / Sad Idle**: Remy weak on the kitchen floor.
3. **Pushing**: search "pushing" (pushing the fridge to barricade).
4. **Looking Around** (S02 deciding).
5. **Zombie Walk**: the working version, so the horde can shamble.
6. *(Nice to have)* **Zombie Punching** (the arm through the door).

Missing ones will be faked with poses I set by hand, with weaker motion. That was the problem with the first video, so these downloads matter.

## Sources
- Food on hand: Census American Housing Survey (82% of households have 3 days of non-perishable food), via [Cambridge, Disaster Medicine & Public Health Preparedness](https://www.cambridge.org/core/journals/disaster-medicine-and-public-health-preparedness/article/household-food-and-water-emergency-preparedness-practices-across-the-united-states/8979E601643EB8751C4C38E82860E950); FEMA 3-day kit guidance.
- Rule of threes (3 days water / 3 weeks food): [Wikipedia](https://en.wikipedia.org/wiki/Rule_of_threes_(survival)), [US Air Force fact sheet](https://www.torch.aetc.af.mil/About/Fact-Sheets/Display/Article/364742/rule-of-threes)
- Hand-digging rate (rough estimates): [Hunker](https://www.hunker.com/13425749/how-to-calculate-how-long-to-dig-a-hole/), [OSHA digging](https://osha.gov/etools/electrical-contractors/installation-repair/digging)

## Video DNA (proposed)
`DNA: STRUCT=Choice elimination (A ✗, B ✗, C ✓) | ENV=suburban house → backyard → street, golden hour | PALETTE=warm amber / water blue | HOOK=door bursting + arm through | CAM=whip-pan between choices | END=match cut to the door`
Differs from part 1 on STRUCT, ENV, PALETTE, HOOK, CAM and END. ✅
