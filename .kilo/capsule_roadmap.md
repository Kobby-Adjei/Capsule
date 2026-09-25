CAPSULE ROADMAP
Kobby builds. Claude explains and unblocks. Written 2026-09-25.

RULES
  You type everything. If I hand you code, read it before you run it.
  One milestone per sitting. Do not start the next until the test passes.
  Commit at the end of every milestone, even the ugly ones.
  Build it in Python. If you later want the State Street credential, porting a
  WORKING service to Spring Boot is far easier than learning servers and Java
  at the same time.

======================================================================
M0  SETUP                                              target: 30 minutes
======================================================================
Goal: an empty project that runs.

  mkdir capsule && cd capsule 
  python3 -m venv .venv
  source .venv/bin/activate          # you should see (.venv) in your prompt
  pip install flask
  pip freeze > requirements.txt
  git init
  printf '.venv/\n*.db\n__pycache__/\n.env\n' > .gitignore

Write app.py with ONE endpoint:

  from flask import Flask
  app = Flask(__name__)

  @app.get("/health")
  def health():
      return {"ok": True}

  app.run(port=5001)

DONE WHEN
  python3 app.py runs, and http://localhost:5001/health shows {"ok": true}
  in your browser. Then: git add -A && git commit -m "M0 health endpoint"

WHY THIS IS A MILESTONE
  Most people lose a day to environment problems. Getting a venv, a git repo
  and one working route out of the way first means every later problem is a
  code problem, not a setup problem.

WATCH OUT
  Port 5000 is taken by AirPlay on a Mac. Use 5001.
  If "flask not found", your venv is not active. Run source .venv/bin/activate.

======================================================================
M1  IT REMEMBERS (in a list)                           target: 1 hour
======================================================================
Goal: push a capsule, pull it back. No database, no auth.

New ideas: POST with a JSON body, reading request.get_json(), a module-level
list that survives between requests.

  CAPSULES = []          # a plain python list at the top of app.py

  POST /capsules   ->  append the incoming dict, return it with an id
  GET  /capsules   ->  return the whole list

Give each capsule an id. Simplest that works:
  import uuid
  cid = "cap_" + uuid.uuid4().hex[:6]

DONE WHEN
  In terminal 1: python3 app.py
  In terminal 2:
    curl -X POST localhost:5001/capsules -H "Content-Type: application/json" \
      -d '{"task":"test","state":"started"}'
    curl localhost:5001/capsules
  The second command shows what the first one sent.

WHY THIS MATTERS
  This is your entire product, working, just forgetful. Everything after this
  is making it durable, safe and addressable. If you only ever finish M1, you
  have still built the thing.

WATCH OUT
  Forgetting the Content-Type header gives you a confusing None from get_json().
  Restarting the server empties the list. That is expected. M2 fixes it.

======================================================================
M2  IT SURVIVES A RESTART                              target: 1-2 hours
======================================================================
Goal: swap the list for SQLite.

New idea: persistence. One table, columns matching what you were putting in
the dict. sqlite3 is in the standard library, nothing to install.

  CREATE TABLE IF NOT EXISTS capsules (
      id TEXT PRIMARY KEY,
      created TEXT,
      task TEXT,
      state TEXT,
      handoff TEXT
  )

Write two small helper functions, save_capsule() and list_capsules(), and have
your endpoints call them. Keep SQL out of the endpoint functions.

DONE WHEN
  Push a capsule. Ctrl+C the server. Start it again. Pull. It is still there.

WHY THIS MATTERS
  This is the moment it stops being a toy. Also: separating "the endpoint" from
  "the storage function" is the single most useful habit in this whole project.

WATCH OUT
  "no such table" means you never ran CREATE TABLE. Run it on every startup,
  IF NOT EXISTS makes that safe.

======================================================================
M3  ADDRESSING                                         target: 1 hour
======================================================================
Goal: a capsule can be aimed at one agent, and closed when finished.

Add two columns: for_who TEXT, status TEXT.
Filter in the pull:

  SELECT ... WHERE status='open' AND (for_who = ? OR for_who = 'any')

DONE WHEN
  Push one with "for":"claude". Pull with ?agent=muse and get [].
  Pull with ?agent=claude and get the capsule.

WHY THIS MATTERS
  This is the tag rule from your own spec, the part the spec left undefined.
  It is one WHERE clause. The hard part was deciding the rule, not writing it.

DECISIONS TO MAKE HERE (write your answers in the README)
  What does pull return when nothing matches? (recommend: empty list, not error)
  What order? (recommend: newest first)
  Does pull return closed capsules? (recommend: no, unless asked)

======================================================================
M4  KEYS                                               target: 1 hour
======================================================================
Goal: not everyone can call it.

New ideas: reading a request header, 401, and the difference between
authentication (who are you) and authorization (what may you see).

  KEYS = {"caps_claude_123": "claude", "caps_muse_456": "muse"}

Read Authorization: Bearer <key>, look up the agent name. If unknown, return
401. Then use that name for the addressing filter, instead of ?agent= from M3.

DONE WHEN
  Right key returns data. Wrong key returns 401. No key returns 401.
  And muse can no longer see claude's capsules by lying in the query string.

WHY THIS MATTERS
  Notice what just happened: the key stopped being about security only, and
  became the thing that identifies the caller. That is why it replaces ?agent=.

======================================================================
M5  APPEND AND PROFILE                                 target: 2 hours
======================================================================
Goal: update a capsule without resending it, and add the second resource.

New idea: a variable in the route.

  @app.post("/capsules/<cid>/append")
  def append(cid):
      ...

Then add the profile endpoints:
  GET  /profile                 the facts, answers, never_claim
  POST /profile/answered        add one answer

Seed the profile from the CAPSULE document already in your Drive. That content
is written, you are just moving it into the database.

DONE WHEN
  You can push a capsule, append a new state to it, and see both the original
  and the update. And GET /profile returns your never_claim list.

WHY THIS MATTERS
  Append is the endpoint that justified building a service instead of a file.
  Everything before this, a Google Doc could have done.

======================================================================
M6  TESTS, README, DEPLOY                              target: half a day
======================================================================
Goal: someone other than you can run it, and it lives on the internet.

  pip install pytest
  tests/test_api.py using Flask's test client. Cover at minimum:
    push then pull returns the capsule
    wrong key returns 401
    a capsule addressed to claude is invisible to muse

  README.md with: what it is, how to run it, and every endpoint with an
  example request and response. Copy the shapes from this roadmap.

  Deploy to Railway. Move KEYS out of the code into environment variables.
  Never commit a real key.

DONE WHEN
  pytest passes. You can curl your Railway URL from your phone and get data.

WHY THIS MATTERS
  This is the milestone that turns the project into something you can put on a
  resume. "I built an API" is weak. "Deployed, tested, documented, with auth"
  is the State Street job description almost word for word.

======================================================================
M7  AN AGENT ACTUALLY USES IT                          target: 2 hours
======================================================================
Goal: the whole point.

Two ways, easiest first:
  a) Put one line in your Claude project instructions: "Before doing any work,
     GET <your railway url>/profile with this key, and GET /capsules."
  b) Wrap the endpoints as an MCP server so it becomes real tools.

Do (a) first. It is one line and it proves the loop.

DONE WHEN
  A brand new chat session, with no explanation from you, already knows you
  have never used GraphQL and does not ask you about Redis.

WHY THIS MATTERS
  Everything before this is plumbing. This is the milestone where you stop
  being the transport layer between your own agents.

======================================================================
WHAT IS DELIBERATELY NOT ON THIS LIST
======================================================================
  A router that decides who gets what     you decide, and you are fast
  Push notifications or webhooks          pull covers it, per your own spec
  Jev or any model inside Capsule         nothing here needs inference
  File upload                             Drive keeps bytes, Capsule keeps pointers
  A frontend                              curl is your frontend for now

  If you find yourself building any of these before M7, you have drifted.

======================================================================
HOW TO TELL ME YOU ARE STUCK
======================================================================
  Paste three things: what you ran, the full error, and what you expected.
  Do not paste the whole file unless I ask. Do not fix it by asking me to
  rewrite it, ask me why it broke. You will learn more and it goes faster.

