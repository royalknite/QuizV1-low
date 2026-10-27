# Render Bandwidth Update (Hindi)

## क्या बदला
- `/testseries` से Mock Test PDF बनाना/भेजना अस्थायी रूप से बंद किया गया है।
- Scheduler bot का `/pdf` command अब PDF reports को enable नहीं करता; यह केवल disabled status बताता है।
- Automatic PDF report delivery पहले से `PDF_REPORTS_ENABLED = False` थी और बंद ही रखी गई है।
- Quiz creation, live quiz/polls, answers, scoring, timers, results, leaderboard, HTML reports, assignment/document handling और PDF/TXT input parsing के अन्य handlers को जानबूझकर नहीं बदला गया।

## जरूरी सीमा
इस बदलाव से कितनी bandwidth बचेगी, यह इस पर निर्भर है कि पहले कितनी PDF बन/भेज रही थीं। 5 GB में 31 दिन चलने की गारंटी बिना deploy के बाद usage मापे नहीं दी जा सकती।

## Deploy के बाद जाँच
1. `/testseries <QUIZ_ID>` भेजें — PDF बंद होने का संदेश आना चाहिए।
2. एक सामान्य live quiz चलाकर answer, timer, result और leaderboard जाँचें।
3. Render Metrics में अगले 24 घंटे का Outbound Bandwidth नोट करें।
