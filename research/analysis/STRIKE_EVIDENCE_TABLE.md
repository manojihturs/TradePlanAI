# STRIKE-001 Evidence Table — TR-001.md

Source: `research/transcripts/TR-001.md` (the ONLY transcript file in the repo; `research/videos/` and the rest of `research/transcripts/` contain nothing but `.gitkeep`).

**Data-quality note (see also STRIKE_EVIDENCE_SUMMARY.md):** `research/analysis/TR-001_ANALYSIS.md` Section 3.1 claims the first-candle strike-selection pattern "recurs across ~11 daily segments." TR-001.md has exactly **one** date header at the top ("Jul 3, 2026", line 25) and no per-segment markers in that sense. What actually recurs are **many different illustrative trading-day walkthroughs** the speaker narrates inside a single continuous video/session — some in an undated, non-timestamped block (lines ~27–1050, itself containing repeated "Jun X, 2026" sub-headers that look like separate source video transcripts concatenated into one file), and some in a timestamped block (lines ~1700 onward, timestamps like `00:15:10`) that reads like a live Q&A/webinar recording. There are in fact **more than 11** distinct day-examples referencing "first candle" top/bottom across the file (occurrences at lines 33, 235, 325, 519, 630, 1063, 1745, 2461, and more not fully reviewed below line 2521 — see Summary for scope limits). The "~11 segments" framing in the ANALYSIS doc should be treated as approximate/unverified, not a structural fact of the source file.

**Scope actually reviewed for this table (UPDATED — full file now covered):** full paragraph-level reading of lines 1–2521 (first pass) plus a second pass covering every remaining "ஃபர்ஸ்ட் கேண்டில்" (first candle) cluster located by `grep` between line 2521 and line 4245 (the true end of the file) — clusters at lines 2646, 2761, 2865, 2982 (excluded, downstream reference), 3036 (excluded, downstream reference), 3102 (excluded, off-topic), 3156-3198, 3479 (excluded, spot-chart sentiment, not strike selection), 3784 (excluded, ATP/seller-perspective concept, unrelated), 3879-3927, and 4088-4139 were all read in full context. The file is confirmed to be a concatenation of roughly 8-9 distinct video transcripts (identifiable by repeated "Hello Traders, welcome to Trade Plan" openings and date/session changes), not "~11 daily segments" as the ANALYSIS doc claims. **This is now a complete review of the entire 4245-line file**, not a partial sample.

| # | Transcript | Timestamp | First Candle Mentioned | Strike Mentioned | Bullish Mentioned | Bearish Mentioned | Bottom Mentioned | Top Mentioned | Open | Close | High | Low | Round Number | Example Strike | Possible Formula | Confidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | TR-001 | Lines 33-40 (no timestamp in source) | Yes | Yes | Yes | No | Yes | No | No | No | No | No | Yes (50) | 24050 | Observed Pattern: speaker calls the first candle "bullish" and states he took the *bottom* of the first candle, rounded to 50, as the strike; explicitly says he did not need to look at the top because a bullish candle removed the need. | High |
| 2 | TR-001 | Lines 235-237 (no timestamp in source) | Yes | Yes | Yes | No | Yes | No | No | No | No | No | No | 23800 | Observed Pattern: "இது வந்து ஒரு புல்லிஷ் கேண்டிலா இருந்ததுனால பாட்டம் ஸ்ட்ரைக்" — bottom strike chosen because the candle was bullish. Same pairing (bullish→bottom) as row 1. | High |
| 3 | TR-001 | Lines 325-329 (no timestamp in source) | Yes | Yes | No | Yes | Yes | Yes | No | No | No | No | No | 2450 (top) / 23950 (bottom) | Observed Pattern: both top and bottom of the first candle are named as strikes (2450 top, 23950 bottom); market approaching from above described as "bearish candle," and the speaker analyzes starting from the TOP strike, choosing a put option there. Opposite pairing from rows 1-2 (bearish→top used first). | High |
| 4 | TR-001 | Lines 519-525 (no timestamp in source) | Yes | Yes | No | No | Yes | Yes | No | No | No | No | No | 350 | Observed Pattern: "ஃபர்ஸ்ட் வந்து டாப் அண்ட் பாட்டம் அஸ்வல் ஃபர்ஸ்ட் கேண்டில் நம்ம எடுக்கும்போது பாட்டம்ல 350 கிடைச்சிருக்கு" — both top and bottom named as the usual reference points; bottom = 350 used as example strike. No explicit bullish/bearish reason given in this instance. | Medium |
| 5 | TR-001 | Lines 630-631 (no timestamp in source) | Yes | Yes | No | No | Yes | Yes | No | No | No | No | No | 23200 (top) / 2300≈23300 (bottom) | Observed Pattern: "ஃர்ஸ்ட் கேண்டிலுடைய டாப் அண்ட் பாட்டம் அது ரெபரன்ஸ்கு எப்பவுமே நம்ம ரெபரன்ஸ்க அத எடுப்போம்" — both top and bottom of first candle stated as the standing reference points used every time; no bullish/bearish qualifier stated at this instance. | Medium |
| 6 | TR-001 | Lines 1059-1072 (no timestamp in source) | Yes | Yes | Yes | No | Yes | No | No | No | No | No | No | 250 (23250) | Observed Pattern: first candle described as "ஸ்ட்ராங்கான புல்லிஷ் கேண்டா" (strong bullish candle); speaker says he "picked from the bottom" ("பாட்டம்ல இருந்து பிக் பண்ணேன்") giving bottom strike 250/23250. Consistent with bullish→bottom pairing (rows 1, 2, 6). | High |
| 7 | TR-001 | 00:15:10-00:22:34 | Yes | Yes | No | No | Yes | No | No | No | Yes | Yes | No | 650 | Observed Pattern: live Q&A walkthrough; speaker takes the low of the first candle of the morning as the trend-point/strike reference (650 put), and separately marks the first candle's high as "மேக்ஸிமம் ஹையா" (the day's maximum high) for the opponent strike. Both a Low (own side) and a High (opponent side) of the first candle are explicitly used as distinct reference values — closer to Open/Close/High/Low framing than the earlier Top/Bottom-of-candle-body framing. | Medium |
| 8 | TR-001 | 00:00:04-00:13:06 | Yes | Yes | No | No | Yes | No | No | Yes | Yes | Yes | Yes (150) | 26150 (i.e. "150") | **Explicitly stated procedure (quoted, not inferred):** speaker describes computing a synthetic "Weekly Future" High/Low from the first candle's Call option High/Low and Put option High/Low ("காலுடைய ஹையும் புட்டுடைய லோவும்... ஹை", "ஹை மைனஸ் லோ", i.e. Weekly-Future-High = Strike + (Call-First-Candle-High − Put-First-Candle-Low), Weekly-Future-Low = Strike − (Call-First-Candle-Low − Put-First-Candle-High) with sign handling as narrated), and also separately uses first-candle Close data for Call and Put ("க்ளோஸ் டேட்டா"). He then chooses the strike **nearest to** that computed weekly-future value as the trend-point strike (150 chosen here). At the time this row was first written it looked like a singular instance — **rows 9-14 below (from the full-file review) confirm this is in fact the speaker's standard, repeatedly-stated general method, not an isolated one-off.** | High |
| 9 | TR-001 | Lines 2646-2664 (no explicit timestamp; embedded in 00:03:22-00:05:26 block) | Yes | Yes | No | Yes | Yes | Yes | No | No | No | No | No | 950 (top) / 900 (bottom) | Observed Pattern: "டாப் ஸ்ட்ரைக் எடுத்துருக்கேன். 950 கால் புட் எடுத்துருக்கேன். ஏன் அப்படின்றதுக்கு காரணம் அது ஹைல இருக்கக்கூடிய ஸ்ட்ரைக் பிரைஸ் அஸ் வெல் அஸ் ஃபர்ஸ்ட் கேண்டில் ஒரு நல்ல ஒரு ஸ்ட்ராங்கான பியரிஷ் கேண்டில்" — top strike (950) chosen first because the first candle was a strong bearish candle. Bottom (900) is separately marked as "first candle's bottom" ("அடுத்த ஸ்ட்ரைக் வந்து 900 விச் இஸ் ஃபர்ஸ்ட் கேண்டிலுடைய பாட்டம்"). Third clean instance of the bearish→top pairing (matches row 3), reinforcing it is not a one-off. | High |
| 10 | TR-001 | Lines 2761-2775 (embedded in 00:05:22-00:08:10 block) | Yes | Yes | Yes | No | Yes | Yes | No | No | Yes | Yes | No | 26200 (top) / 26150 (bottom) | **Reconciling statement (quoted):** "நம்மளோட ஸ்ட்ரைக் பிரைஸ் எப்பவுமே பியூச்சர் அடிப்படையில் தான் தொடங்குவோம் அப்படின்னு நம்ம சொல்லி இருக்கோம். அதன் அடிப்படையில பியூச்சர் ஓட ஹை அண்ட் லோவ நீங்க பார்க்கலாம். சப்ஸ்டி கேண்டிலோட ஹை அண்ட் லோ. அப்படி பார்க்கும்போது 26200ம் 26150... இந்த ரெண்டு ஸ்ட்ரைக் வந்து டாப் அண்ட் பாட்டமா எனக்கு." — "We've always said our strike price starts based on the Future. Based on that you look at the Future's High and Low — [i.e.] the candle's High and Low. Looking at it that way, 26200 and 26150 — these two strikes are top and bottom for me." This is the speaker explicitly equating "Future's High/Low" (row 8's synthetic mechanism) with "the first candle's top and bottom" (rows 1-6's language) — they are stated to be **the same quantity**, not two competing mechanisms. Also repeats bullish→bottom pairing ("150 என்பது பாட்டம் ஸ்ட்ரைக் எஸ் அப்ப பாட்டம்ல கால் தான் டாமினேட் பண்ணி இருக்கணும்"). | High |
| 11 | TR-001 | Lines 2865-2895 (embedded in 00:05:29-00:10:13 block) | Yes | Yes | Yes | No | Yes | Yes | No | No | Yes | Yes | Yes (strike-interval rounding) | 25400 (top) / 25300 (bottom) | **Explicit formula statement (quoted):** "வீக்லி ஃியூச்சர்டைய ஓபன் ஏடிஎம் ஸ்ட்ரைக்க பேஸ் பண்ணி நம்ம கால்குலேட் பண்ணி ஃபர்ஸ்ட் 5 மினிட்ஸ் ஹை அண்ட் லோவ கால்குலேட் பண்ணும் இதுதான் அதனுடைய பர்பஸ்... ஹை வந்து 25393 வந்திருக்கு லோ வந்து 25288.95 வந்துருக்கு. சோ டாப் ஸ்ட்ரைக்கா எனக்கு 25400 கிடைச்சிருக்கு. பாட்டம் ஸ்ட்ரைக்கா 25300 கிடைச்சிருக்கு... நம்ம ஏற்கனவே பார்முலால கொடுத்திருக்கோம்." — "Based on the Weekly Future's Open ATM strike, we calculate the first 5-minute candle's High and Low — that's the purpose. High came to 25393, low came to 25288.95. So I got 25400 as top strike, 25300 as bottom strike... we've already given you the formula [in an earlier video]." This is the clearest explicit statement in the whole file: compute Weekly-Future first-candle High/Low, then round each to the **nearest listed strike** to get Top Strike and Bottom Strike. Also repeats bearish→top pairing: "நான் டாப் ஸ்ட்ரைக்ல இருந்து ஆரம்பிச்சேன். அதுக்கு ரீசன் ஏன்னா எனக்கு தெரிஞ்சிருச்சு அது ஒரு ஸ்ட்ராங்கான பியரிஷ் கேண்டில்." | High |
| 12 | TR-001 | Lines 3195-3202 (00:53:49-01:04:52 block, live Q&A) | Yes | Yes | No | Yes | Yes | Yes | No | No | No | No | No (nearest-strike, general) | 400 (top, example) | **General rule stated directly in answer to a viewer's general question, not tied to one day's example:** Viewer asks "Palapudu சார் ட்ரெண்ட் பாயிண்ட் கண்டுபிடிக்க ஸ்ட்ரைக் எப்படி சூஸ் பண்றது?" (how do you choose the strike to find the trend point?). Speaker answers: "ஃபர்ஸ்ட் கேண்டிலோட ஹை சார். வீக்லி ஃபியூச்சர் ஓட ஃபர்ஸ்ட் கேண்டிலோட ஹை அண்ட் லோவ மட்டும் பாருங்க சார். அங்க இருந்து ஆரம்பிங்க சார்." Then, applying it: "400 தான் நியரஸ்ட் ஸ்ட்ரைக் அதுதான் நம்ம எடுக்கணும்." ("400 is the nearest strike, that's what we take.") This is the single strongest piece of evidence that the mechanism is a **general, repeatable rule** ("First candle High/Low of the Weekly Future, take the nearest strike") rather than an ad hoc per-day observation — it is given as a direct, generalized answer to a direct question, independent of any specific trading day's narrative. | High |
| 13 | TR-001 | Lines 3879-3927 (00:02:23-00:09:44 block, SENSEX expiry day) | Yes | Yes | Yes (2nd candle) | No | Yes | Yes | No | No | No | No | Yes (100-pt gap, "closer of the two") | 750 (top) / 650 (bottom) | **Important nuance — Doji/ambiguous first candle:** "இதனோட ஃபர்ஸ்ட் கேண்டில் முடிவுல பாருங்க. ஒரு நல்ல ஒரு டோஜி கேண்டில் மாதிரி... அதோட டாப் ஸ்ட்ரைக் அண்ட் பாட்டம் ஸ்ட்ரைக் நான் பாப்பேன்." When the first candle itself is a Doji (no clear bullish/bearish direction), the speaker takes **both** top and bottom strikes and explicitly defers the choice of which to trade from to the **second** 5-minute candle's direction: "செகண்ட் கேண்டில் ஒரு நல்ல ஒரு புல்லிஷ் கேண்டிலா இருக்கும் பட்சத்துல நான் பாட்டம்ல இருந்தே ஸ்டார்ட் பண்றேன்." **Directly states there is no fixed rule for which side to start from:** "நம்ம எங்க இருந்து ஸ்டார்ட் பண்ணனும்ன்றது வந்து ரூல் கிடையாது. இட்ஸ் அப்டு அந்த டைமிங்ல என்ன நடக்குதுன்றத புரிஞ்சு அதுக்கு ஏத்த மாதிரி நம்ம ஃப்ளோல போகிறோம்." Also states relevance/nearness is judged on **both** number and price-gap basis, not pure mechanical rounding: "நம்பர் பேசிஸ்லயும் நீங்க ரெலவன்ட் பாக்கணும். கேப் பேசிஸ்லயும் நீங்க ரெலவன்ட் பாக்கணும்... எது ரொம்ப நெருக்கமா அமையுதோ அதுல எது பெட்டரோ அத சூஸ் பண்ணிக்கணும்." | High |
| 14 | TR-001 | Lines 4088-4109 (00:00:34-00:04:56 block, Pongal-week Friday analysis) | Yes | Yes | Yes | Yes | Yes | Yes | No | No | Yes | Yes | Yes | 26200 (top) / 26100 (bottom) | **Decisive reconciliation (quoted):** "ஈவன் ஃர்ஸ்ட் ரெண்டு மூணு கேண்டிலே பாத்தீங்கன்னா நிப்டி ஸ்பாட்ல வந்து உங்களுக்கு அப்சைடுல மூவ் ஆன மாதிரி இருக்கும். ஆனா வீக்லி ஃியூச்சர்ல பாத்தீங்கன்னா ஒரு மாதிரி டவுன்சைடு வித் கன்சாலிடேஷன் மாதிரி தெரியும்." — "Even if the first two-three candles look like an upside move on NIFTY spot, if you look at the Weekly Future it looks like a downside move with consolidation." This proves that "first candle" in the speaker's strike-selection language means the **computed Weekly-Future candle**, not the raw index/spot candle — the two can even point in opposite directions, and the speaker explicitly warns viewers about this discrepancy. Then, confirming procedure: "ஃபர்ஸ்ட் கேண்டில் கக்ளோஸ் ஆச்சு. நான் என்ன யோசிச்சேன்னா மேல வந்து ஒரு 26200 ஸ்ட்ரைக்கும் கீழ 26100 ஸ்ட்ரைக்கும் தான் வந்து ரெடி ஆயிருந்துச்சு. அதா ஃபர்ஸ்ட் ஒரு கேண்டில் முடியும் போது ஹை அண்ட் லோ இருக்கும். அப்ப ஹைக்கு ஒரு ஸ்ட்ரைக்கும் லோக்கு ஒரு ஸ்ட்ரைக்கும் கிடைக்கும்ல. சோ அத பேஸ் பண்ணி நான் அப்படிதான் எடுத்துக்கிட்டேன்." | High |

## Detail Subsections

### 1. TR-001, Lines 33-40
**Exact Quote (Tamil, verbatim):**
> "நமக்கு ரொம்ப பெர்ஃபெக்ட்டா ஒர்க் அவுட் ஆச்சு நம்மளோட ஸ்ட்ரைக் ப்ரைஸ் பாத்தீங்கன்னா ஃபர்ஸ்ட் கேண்டலோட அடிப்படையில பாக்கும் போது பாட்டம் வந்து நம்மளுக்கு 24050 நான் சூஸ் பண்ணி இருந்தேன் ரொம்ப நடுவுல தான் அதாவது 74 பாயிண்ட் சம்திங் தான் இருந்துச்சு பட் நம்ம வந்து ஒரு புல்லிஷ் கேண்டிலா இருக்கவே நம்ம 50ய எடுத்துக்கிட்டோம் சோ 24050 கேண்டில் ஸ்ட்ரைக் ப்ரைஸ் நம்ம பாட்டமா எடுத்துக்கிட்டோம் டாப் பாக்க வேண்டிய தேவை ஏற்படல பிகாஸ் உங்களுக்கு பாத்தீங்கன்னா ஒரு புல்லிஷ் கேண்டில் அதுக்கப்புறம் பெர்தரா எந்த ஒரு டவுன் சைட் மூவமும் ஏற்படல."

**English Translation (constructed, not source text):** "It worked out very perfectly for us. When you look at our strike price based on the first candle, the bottom came to 24050 for us — I had chosen it. It was very much in the middle, i.e., something around 74 points, but since it was a bullish candle, we took the 50 [round number]. So we took 24050 as the candle strike price, the bottom. There was no need to look at the top, because as you can see, after a bullish candle there was no downside movement further."

**Evidence Level:** Original Transcript (per research/KNOWLEDGE_SOURCES.md)
**Confidence:** High
**Notes:** This is the row already extracted in the earlier STRIKE-001 milestone.

### 2. TR-001, Lines 235-237
**Exact Quote (Tamil, verbatim):**
> "ஓகே. சோ வித் தட் நோட் இந்த வீடியோல நம்ம இன்னைக்கு பாக்க போறது பாத்தீங்கன்னா யூசுவலா நம்ம வீக்லி அடிப்படையில ஃபர்ஸ்ட் கேண்டில் டாப் அண்ட் பாட்டம் பாப்போம். இன்னையோட பாட்டம் ஸ்ட்ரைக் சின்ஸ் இது வந்து ஒரு புல்லிஷ் கேண்டிலா இருந்ததுனால பாட்டம் ஸ்ட்ரைக் பாத்தீங்கன்னா 23800."

**English Translation:** "OK. With that note, in today's video what we're going to look at — usually, on a weekly basis, we look at the first candle's top and bottom. Today's bottom strike — since this was a bullish candle, the bottom strike, if you look, is 23800."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** Same bullish→bottom pairing as row 1, different trading day example (23800 vs 24050).

### 3. TR-001, Lines 325-329
**Exact Quote (Tamil, verbatim):**
> "சரிங்களா சோ அஸ் யூசுவல் நம்மளுடைய முந்தைய காணொளியில நம்ம சொல்லி இருக்கோம் ஃியூச்சர்ல ஃபர்ஸ்ட் கேண்டில் ஃபார்ம் ஆகும்போது டாப் அண்ட் பாட்டம் என்னன்னு பாப்போம் சோ இன்னையோட ஃபர்ஸ்ட் கேண்டில் டாப் பாத்தோம்னா 2450 ஸ்ட்ரைக்கும் பாட்டம் வந்து 23950 ஸ்ட்ரைக்கும் அமைஞ்சிருந்தது இதுதான் அமைஞ்சிருந்த சோ மேல இருந்து இப்ப மார்க்கெட் வந்து ஒரு பியரிஷ் கேண்டிலா இருக்கும் பட்சத்துல அது மட்டும் இல்லாம நம்ம லெவலுக்கு வந்து மேல இருந்து இப்படி வரதுனால நம்ம ரிவர்சலுக்கு எக்ஸ்பெக்ட் பண்றோம். சோ அந்த அடிப்படையில டாப்ல இருந்து அனலைஸ ஸ்டார்ட் பண்றோம்."

**English Translation:** "As usual, as we said in our previous video, when the first candle forms in the [weekly] future, let's see what its top and bottom are. So today's first candle top came out to strike 2450 and the bottom came out to strike 23950. Since the market is now coming down from above in what appears to be a bearish candle, and since it's coming down from above toward our level, we expect a reversal. So on that basis we start analyzing from the top."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** Bearish candle example — top strike (2450) is the one first used for analysis, opposite emphasis from rows 1/2/6 (bullish→bottom). Both top and bottom are named as strikes in this instance (unlike row 1 where "no need to look at top").

### 4. TR-001, Lines 519-525
**Exact Quote (Tamil, verbatim):**
> "போறோம் ஒன்னு நமக்கு வந்து ஏன் வந்து வந்து இந்த இடத்துல வந்து ஃபர்ஸ்ட் கேண்டில் நம்ம எப்பவுமே யூசுவலா பாக்குற மாதிரிதான் ஃபர்ஸ்ட் கேண்டில் டாப் அண்ட் பாட்டம் நம்ம எடுப்போம். ... சோ இதுக்கு ஃபர்ஸ்ட் வந்து டாப் அண்ட் பாட்டம் அஸ்வல் ஃபர்ஸ்ட் கேண்டில் நம்ம எடுக்கும்போது பாட்டம்ல 350 கிடைச்சிருக்கு."

**English Translation:** "...one of the things we're going to discuss is this: as usual, we always look at the first candle — we take the first candle's top and bottom. ...So for this, first, top and bottom as usual — when we take the first candle, the bottom gave us 350."

**Evidence Level:** Original Transcript
**Confidence:** Medium (no bullish/bearish reasoning explicitly stated for why bottom was picked in this instance, unlike rows 1/2/6)
**Notes:** Reinforces "top and bottom of first candle, always" as a stated habitual reference; strike example 350.

### 5. TR-001, Lines 630-631
**Exact Quote (Tamil, verbatim):**
> "சோ அஸ் யூசுவல் நம்மளுடைய முந்தைய காணொளியில நம்ம சொல்லி இருக்கோம் ஃியூச்சர்ல ஃபர்ஸ்ட் கேண்டில் ஃபார்ம் ஆகும்போது டாப் அண்ட் பாட்டம் என்னன்னு பாப்போம் ... [distinct occurrence, line 630] சோ ஃர்ஸ்ட் கேண்டிலுடைய டாப் அண்ட் பாட்டம் அது ரெபரன்ஸ்கு எப்பவுமே நம்ம ரெபரன்ஸ்க அத எடுப்போம்."

**English Translation:** "...the top and bottom of the first candle — that is always what we take as our reference."

**Evidence Level:** Original Transcript
**Confidence:** Medium
**Notes:** Same standing-reference framing as row 4; no bullish/bearish qualifier at this exact instance.

### 6. TR-001, Lines 1059-1072
**Exact Quote (Tamil, verbatim):**
> "அன்ஃபார்சுனேட்லி மார்க்கெட் வந்து ஓபன் ஆகி ஃபர்ஸ்ட் கேண்டில் பாத்தீங்கன்னா, டாப் அண்ட் பாட்டம் இந்த கேண்டில கிராஸ் பண்ணிதான் ஆனா அந்த கேண்டிலோட ஸ்ட்ரக்சர் பாக்கும்போது ஒரு ஸ்ட்ராங்கான புல்லிஷ் கேண்டா தான் எனக்கு தெரிஞ்சது. ... அப்போ நம்ம அனாலிசிஸ் ஸ்டார்ட் பண்ணனும்னா ஏதாவது ஒரு டைரக்ஷன்ல இருந்து பிக் பண்ணனும். சோ நான் இன்னைக்கு பாத்தீங்கன்னா பாட்டம்ல இருந்து பிக் பண்ணேன். இன்னையோட பாட்டம் ஸ்ட்ரைக் பாத்தீங்கன்னா 250 அமைஞ்சது 23250 தான் இன்னையோட பாட்டம் ஸ்ட்ரைக்."

**English Translation:** "Unfortunately, when the market opened and I looked at the first candle, top and bottom — this candle crossed [levels], but when I looked at the structure of that candle, I understood it to be a strong bullish candle. ...So to start our analysis, we have to pick from some direction. So today I picked from the bottom. Today's bottom strike came out to 250, i.e. 23250 is today's bottom strike."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** Third instance of bullish→"pick from bottom" pairing (with rows 1, 2). Speaker explicitly frames the choice of top-vs-bottom as a deliberate pick driven by candle direction, not an automatic rule stated once and for all.

### 7. TR-001, Timestamp 00:15:10-00:22:34
**Exact Quote (Tamil, verbatim, excerpt):**
> "...ஃபர்ஸ்ட் கேண்டில் பாருங்க எப்படி போயிருக்கு அடுத்தது பாருங்க... இப்போ இந்த இடத்துல பாத்தீங்கன்னா ஃபர்ஸ்ட் கேண்டில் நான் ஏற்கனவே உங்களுக்கு கொடுத்திருந்த மாதிரி தான் ஆக்சுவலா ஃபர்ஸ்ட் கேண்டில்லையே பாத்தீங்கன்னா ஐ திங்க் 650 வந்து பாட்டம் ஸ்ட்ரைக்கா கொடுத்துருந்தேன். ... 650 கால் வந்து இவனுடைய லோ வந்து ஆக்சுவலா காலையில இந்த லோ தான் இருந்துச்சு இதுதான் ஃபர்ஸ்ட் காலையில இருந்த லோ ஓகே ட்ரெண்ட் பாயிண்ட் லோ... சோ மார்னிங் பாத்தீங்கன்னா ஃபர்ஸ்ட் கேண்டில்ல வச்ச ஹை தான் மேக்ஸிமம் ஹையா இருந்துச்சு."

**English Translation:** "...look at how the first candle went, look at what's next... At this point, looking at the first candle — same as I already told you — actually looking at the first candle itself, I think I had given 650 as the bottom strike. ...650 call — its low is actually the low that was there in the morning; this is the first morning low, OK, trend-point low... So looking at the morning, the high set in the first candle was the maximum high [for the whole day]."

**Evidence Level:** Original Transcript
**Confidence:** Medium
**Notes:** This is a live Q&A/webinar segment (timestamped region) walking through a fresh example (Monday's market, 650 strike) in response to a participant's question, not a pre-scripted video narration. Same 30-second-window timestamps immediately before (00:14:40, 00:15:10) and after (00:15:39, 00:16:09) are included above for context per the task's proximity requirement.

### 8. TR-001, Timestamp 00:00:04-00:13:06
**Exact Quote (Tamil, verbatim, excerpt — this is a long explicit walkthrough, excerpted for length):**
> "ஃபர்ஸ்ட் கேண்டில் ஓபன் ஆனதுமே நம்ம வீக்லி ஃியூச்சர எடுத்துப்போம். ஓகே அந்த வீக்லி பியூச்சரோட கால்குலேஷன் ஹை ஃபர்ஸ்ட் கேண்டிலோட ஹை லோ ஓபன் உங்களுக்கு என்னென்ன டேட்டா எனக்கு ஹை லோவே போதுமானது... ஃபர் எக்ஸாம்பிள் ஃபர்ஸ்ட் கேண்டிலுடைய காலுடைய ஹை அண்ட் லோ என்ன? கால் வந்து 153 113... புட்டுடைய ஃபர்ஸ்ட் கேண்டில் ஹை அண்ட் லோ என்ன இது? 95.5 95... இப்ப நம்ம வீக்லி ஃியூச்சர்ட ஹை அண்ட் லோ கால்குலேட் பண்ண போறோம்... ஹை அப்படினாலே காலுடைய ஹையும் புட்டுடைய லோவும்... 153-72 போட்டீங்கன்னா 91... 150 பிளஸ் 82 ... 26 232 இதுதான் ஹை... ஸ்ட்ரைக் ப்ரைஸ் கூட மைனஸ் பண்ணனும்... 268 இதுதாங்க லோ... இப்ப சொல்லுங்க ஹைக்கு ஈக்குவலன்ட்டான ஸ்ட்ரைக்க சூஸ் பண்ணனும்னா என்ன சூஸ் பண்ணுவீங்க 26 250 சூஸ் பண்ணலாமா அதுதான ரொம்ப க்ளோசரா இருது..."

**English Translation:** "As soon as the first candle opens, let's take our weekly future [figure]. For that weekly future calculation, high — first candle's high, low, open — what data do you need? For me, high and low are enough... For example, what's the first candle's Call high and low? Call is 153, 113... What's the Put's first candle high and low? 95.5, 95... Now we're going to calculate the weekly future's high and low... For the high, that means the Call's high and the Put's low... 153 minus 72 [note: figure inconsistent in the narrated arithmetic, see Notes] gives 91... 150 plus 82... 26232, that's the high... For the low you also have to subtract the strike price... 268 [i.e. 26268], that's the low... Now tell me, if you want to choose the strike equivalent to the high, what would you choose? Would you choose 26250? That's the closest one..."

**Evidence Level:** Original Transcript
**Confidence:** High (the described procedure is explicit and stated multiple times in this segment), but treat as a **singular instance** within the reviewed scope — see Conflicts/Mathematical Clues in Summary.
**Notes:** This instance is structurally different from rows 1-6: it is not "strike = top or bottom of first candle" but "compute a synthetic Weekly-Future High/Low from the first candle's Call-option and Put-option High/Low/Close data, then pick the strike nearest that computed value." The speaker's own arithmetic in the transcript is imprecise/inconsistent in places (e.g., "153-72" then "91" then later "81" for what should be the same subtraction) — this is flagged as a transcription/spoken-math inconsistency, not resolved or corrected here per the no-invention constraint.

### 9. TR-001, Lines 2646-2664
**Exact Quote (Tamil, verbatim, excerpt):**
> "டாப் ஸ்ட்ரைக் எடுத்துருக்கேன். 950 கால் புட் எடுத்துருக்கேன். ஏன் அப்படின்றதுக்கு காரணம் அது ஹைல இருக்கக்கூடிய ஸ்ட்ரைக் பிரைஸ் அஸ் வெல் அஸ் ஃபர்ஸ்ட் கேண்டில் ஒரு நல்ல ஒரு ஸ்ட்ராங்கான பியரிஷ் கேண்டில் ஓகேவா. சோ அப்ப எனக்கு டாப் ஸ்ட்ரைக் 950 அமைஞ்சதுனால நான் ஃபர்ஸ்ட் 950-ல இருந்து ஆரம்பிக்கிறேன் என்னுடைய அனாலிசிஸ்."

**English Translation:** "I've taken the top strike. I've taken 950 CE/PE. The reason: it's the strike price at the high, as well as the first candle being a good, strong bearish candle. So the top strike came out as 950, so I start my analysis first from 950."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** Third clean instance of bearish→top pairing (with row 3), confirming this is not a single fluke. Both top (950) and bottom (900, "first candle's bottom") are marked as anchors in the same segment.

### 10. TR-001, Lines 2761-2775
**Exact Quote (Tamil, verbatim, excerpt):**
> "நம்மளோட ஸ்ட்ரைக் பிரைஸ் எப்பவுமே பியூச்சர் அடிப்படையில் தான் தொடங்குவோம் அப்படின்னு நம்ம சொல்லி இருக்கோம். அதன் அடிப்படையில பியூச்சர் ஓட ஹை அண்ட் லோவ நீங்க பார்க்கலாம். சப்ஸ்டி கேண்டிலோட ஹை அண்ட் லோ. அப்படி பார்க்கும்போது 26200ம் 26150 ... இந்த ரெண்டு ஸ்ட்ரைக் வந்து டாப் அண்ட் பாட்டமா எனக்கு."

**English Translation:** "We've always said our strike price starts based on the Future. Based on that, you can see the Future's high and low — [i.e.] the candle's high and low. Looking at it that way, 26200 and 26150 — these two strikes are top and bottom for me."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** **Key reconciling statement.** Directly equates "Future's high/low" (row 8's synthetic computed quantity) with "the [first] candle's top and bottom" (rows 1-6's plain-language framing) — stated as the same thing, not two competing methods.

### 11. TR-001, Lines 2865-2895
**Exact Quote (Tamil, verbatim, excerpt):**
> "வீக்லி ஃியூச்சர்டைய ஓபன் ஏடிஎம் ஸ்ட்ரைக்க பேஸ் பண்ணி நம்ம கால்குலேட் பண்ணி ஃபர்ஸ்ட் 5 மினிட்ஸ் ஹை அண்ட் லோவ கால்குலேட் பண்ணும் இதுதான் அதனுடைய பர்பஸ் ஆக்சுவலா அதுதான் பர்பஸ் ... ஹை வந்து 25393 வந்திருக்கு லோ வந்து 25288.95 வந்துருக்கு. சோ டாப் ஸ்ட்ரைக்கா எனக்கு 25400 கிடைச்சிருக்கு. பாட்டம் ஸ்ட்ரைக்கா 25300 கிடைச்சிருக்கு. இது எனக்கு கிடைச்ச ஸ்ட்ரைக் பிரைஸ் பேஸ்ட் ஆன அந்த வேல்யூவ பேஸ் பண்ணி ... நம்ம ஏற்கனவே பார்முலால கொடுத்திருக்கோம் அந்த பார்முலா படி தான் இதுல போட்டுருக்கோம்."

**English Translation:** "Based on the Weekly Future's Open ATM strike, we calculate — calculating the first 5-minute [candle's] high and low is the whole purpose of it. ... The high came to 25393, low came to 25288.95. So I got 25400 as the top strike, 25300 as the bottom strike. This is the strike price I got, based on that computed value... we already gave the formula [in an earlier video], we've plugged it in per that formula here."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** The single clearest explicit statement of "the formula" in the entire file: compute the Weekly-Future's first-5-minute-candle High/Low (row 8's mechanism), then round each to the nearest listed option strike to get Top Strike and Bottom Strike. Also repeats bearish→top pairing in the same segment.

### 12. TR-001, Lines 3195-3202 (Live Q&A)
**Exact Quote (Tamil, verbatim):**
> "வேற பாலபுடு சார் ட்ரெண்ட் பாயிண்ட் கண்டுபிடிக்க ஸ்ட்ரைக் எப்படி சூஸ் பண்றது? ட்ரெண்ட் பாயிண்ட் கண்டுபிடிக்க ஸ்ட்ரைக் அதான் சொன்னேன் ஃபர்ஸ்ட் கேண்டிலோட ஹை சார் வீக்லி ஃபியூச்சர் ஓட ஃபர்ஸ்ட் கேண்டிலோட ஹை அண்ட் லோவ மட்டும் பாருங்க சார் அங்க இருந்து ஆரம்பிங்க சார். ... 400 தான் நியரஸ்ட் ஸ்ட்ரைக் அதுதான் நம்ம எடுக்கணும் அததான் நம்ம ட்ரெண்ட் பாயிண்ட்டா பாக்கணும்."

**English Translation:** "[Viewer:] 'Palapudu sir, how do you choose the strike to find the trend point?' [Speaker:] 'To find the trend point strike, like I said — the first candle's high, sir. Just look at the Weekly Future's first candle's high and low, sir. Start from there, sir.' ... '400 is the nearest strike — that's what we take, that's what we consider as our trend point.'"

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** This is the strongest evidence that the mechanism is a **stated general rule**, not a one-off per-day observation: it is given as a direct, generalized answer to a viewer's direct, generic question ("how do you choose the strike"), independent of any specific day's narrative, and explicitly names "nearest strike" as the selection criterion.

### 13. TR-001, Lines 3879-3927 (SENSEX expiry day)
**Exact Quote (Tamil, verbatim, excerpt):**
> "இதனோட ஃபர்ஸ்ட் கேண்டில் முடிவுல பாருங்க. ஒரு நல்ல ஒரு டோஜி கேண்டில் மாதிரி உங்களுக்கு தெரியும். ... அதோட டாப் ஸ்ட்ரைக் அண்ட் பாட்டம் ஸ்ட்ரைக் நான் பாப்பேன். அண்ட் இது இது வந்து ஒரு பையிங் பிரஷர் செல்லிங் பிரஷரை எடுக்க முடியாதுனா நம்ம டாப் அண்ட் பாட்டம் எடுத்துக்கலாம். ... செகண்ட் கேண்டில் ஒரு நல்ல ஒரு புல்லிஷ் கேண்டிலா இருக்கும் பட்சத்துல நான் பாட்டம்ல இருந்தே ஸ்டார்ட் பண்றேன். நல்லா புரிஞ்சுக்கோங்க. நம்ம எங்க இருந்து ஸ்டார்ட் பண்ணனும்ன்றது வந்து ரூல் கிடையாது. இட்ஸ் அப்டு அந்த டைமிங்ல என்ன நடக்குதுன்றத புரிஞ்சு அதுக்கு ஏத்த மாதிரி நம்ம ஃப்ளோல போகிறோம். ... நம்பர் பேசிஸ்லயும் நீங்க ரெலவன்ட் பாக்கணும். கேப் பேசிஸ்லயும் நீங்க ரெலவன்ட் பாக்கணும் ... எது ரொம்ப நெருக்கமா அமையுதோ அதுல எது பெட்டரோ அத சூஸ் பண்ணிக்கணும்."

**English Translation:** "Look at how this first candle ended — you can see it's like a nice Doji candle. ... I'll look at its top strike and bottom strike. And if [the candle] can't show clear buying or selling pressure, we can take [both] the top and bottom. ... If the second candle turns out to be a good bullish candle, then I start from the bottom. Understand this well: there is NO rule for where we start from. It depends on understanding what's happening at that time, and we flow along with that accordingly. ... You have to check relevance both on a number basis and a gap basis... whichever is closer, whichever is better — you choose that."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** Important nuance/qualifier on the general rule: (a) when the first candle itself is directionless (Doji), both top and bottom strikes are kept as candidates and the top/bottom starting choice is explicitly deferred to the next candle's direction; (b) the speaker explicitly denies that top-vs-bottom starting choice is a fixed rule; (c) "nearest strike" selection is described as judged by both numeric and gap-based relevance, not pure mechanical rounding.

### 14. TR-001, Lines 4088-4109 (Pongal-week Friday analysis)
**Exact Quote (Tamil, verbatim, excerpt):**
> "ஃபர்ஸ்ட் கேண்டில் வந்து ஒரு நல்ல ஒரு புல்லிஷ் கேண்டிலா ஃபார்ம் ஆச்சு. ஆனா நீங்க வீக்லி ஃபியூச்சர் கால்குலேட் பண்ணி அதனுடைய ஹை அண்ட் லோ ஓபன் க்ளோஸ் எல்லாத்தையுமே கால்குலேட் பண்ணிங்கன்னா அது ஒரு ஸ்ட்ராங்கான பியரிஷ் கேண்டிலா இருந்துச்சு. ஈவன் ஃர்ஸ்ட் ரெண்டு மூணு கேண்டிலே பாத்தீங்கன்னா நிப்டி ஸ்பாட்ல வந்து உங்களுக்கு அப்சைடுல மூவ் ஆன மாதிரி இருக்கும். ஆனா வீக்லி ஃியூச்சர்ல பாத்தீங்கன்னா ஒரு மாதிரி டவுன்சைடு வித் கன்சாலிடேஷன் மாதிரி தெரியும். ... ஃபர்ஸ்ட் கேண்டில் கக்ளோஸ் ஆச்சு. நான் என்ன யோசிச்சேன்னா மேல வந்து ஒரு 26200 ஸ்ட்ரைக்கும் கீழ 26100 ஸ்ட்ரைக்கும் தான் வந்து ரெடி ஆயிருந்துச்சு. அதா ஃபர்ஸ்ட் ஒரு கேண்டில் முடியும் போது ஹை அண்ட் லோ இருக்கும். அப்ப ஹைக்கு ஒரு ஸ்ட்ரைக்கும் லோக்கு ஒரு ஸ்ட்ரைக்கும் கிடைக்கும்ல. சோ அத பேஸ் பண்ணி நான் அப்படிதான் எடுத்துக்கிட்டேன்."

**English Translation:** "The first candle formed as a nice bullish candle. But if you calculate the Weekly Future — calculating its high, low, open, close, all of it — it turned out to be a strong bearish candle. Even the first two-three candles, if you look at NIFTY spot, will look like they moved upside. But if you look at the Weekly Future, it looks more like a downside move with consolidation. ... The first candle closed. What I thought was: there was a 26200 strike ready above and a 26100 strike ready below. Because when a first candle finishes, there's a high and a low. So there's one strike for the high and one strike for the low. Based on that, I picked it that way."

**Evidence Level:** Original Transcript
**Confidence:** High
**Notes:** **Decisive reconciliation.** Proves that "first candle" in the strike-selection language always refers to the *computed Weekly-Future candle*, not the raw NIFTY spot/index candle — the two can even point in opposite directions on the same day, and the speaker explicitly warns viewers about this. This resolves the previously-flagged Conflict #2 (literal candle top/bottom vs. synthetic Weekly-Future high/low): they are the same mechanism, described in plain language ("top/bottom") in some segments and in explicit computed-formula language in others.
