# Bandwidth fix (Render free 5 GB) — kya badla

## 1. Asli suspect fix (bot.py, MongoDB pool)
Pehle: `minPoolSize=10` + `maxIdleTimeMS=30000` (dono Mongo clients mein).
Matlab idle connections 30 sec baad band hoke turant dobara ban rahe the (har baar TLS + login),
24x7, chahe user ho ya na ho. Yeh Render ke "Service-Initiated" flat ~17 MB/ghanta se match karta hai.
Ab: `minPoolSize=0`, `maxIdleTimeMS=600000`. Quiz/DB ka kaam same rahta hai.
(Yeh code se anumaan hai, maine live traffic nahi naapa. 24 ghante baad Render Metrics mein check karo.)

## 2. Bandwidth guard (naya `bw_guard.py`)
- Bot ke Telegram sends ka *estimate* gina jaata hai. Owner `/bw` bhej kar dekh sakta hai.
- Daily budget (default 150 MB) ka 70% cross hone par: promo messages band + explanation 100 char.
- 100% cross hone par: explanation bhi band.
- Questions, options, timer, scoring, result, schedule, quiz banana — kuch nahi chhua gaya.
- Band karna ho: env `BW_GUARD_ENABLED=false`.

## 3. Private quiz lean mode (default ON)
Private chat mein har user ko har poll alag jaata hai, isliye wahi sabse zyada bandwidth khata hai.
Ab private quiz mein poll ka *explanation* aur promo nahi bheje jaate (poll size ~20-30% kam).
Question, options, timer, score, result sab same. Group quiz mein explanation pehle jaisa rehta hai.
Wapas chahiye to env `BW_PRIVATE_LEAN=false`.

## Deploy ke baad
1. Render mein redeploy karo.
2. 24 ghante baad Metrics mein Outbound Bandwidth dekho (pehle ~400 MB/din tha).
3. `/bw` ka number Render se milao; alag ho to `BW_CALIBRATION` set karo.
4. Fir bhi zyada ho to: group mode use karo, ya Render mein card add karo (~$15 / 100 GB).
