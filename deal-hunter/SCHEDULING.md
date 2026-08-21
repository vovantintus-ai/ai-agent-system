# Running Deal Hunter on a schedule

The agent is a single-run script (`run.py`). To make it "autonomous" you just
need something to call it repeatedly and keep its state between runs. Two ways.

## A) Local cron (recommended when you have a machine with open network)

The pure pipeline needs no network, but the **real** sources (rss/reddit) do —
so run this where outbound HTTPS to your target site is allowed (your PC, a VPS,
a Raspberry Pi that's on anyway).

1. Install deps once:

   ```bash
   cd deal-hunter
   python3 -m pip install -r requirements.txt
   ```

2. Create `config.yaml` from the example and point it at a real source:

   ```yaml
   sources:
     - type: reddit
       subreddit: buildapcsales      # or a local buy/sell sub
       category: deals
       user_agent: "deal-hunter/0.1 (contact: you@example.com)"
     # - type: rss
     #   url: "https://<classifieds-site>/search.rss?q=makita"
     #   category: tools
   watch_terms: [urgent, "quick sale", makita, bosch]
   baselines:   { deals: 300, tools: 200 }
   min_discount: 0.20
   state_path: state/seen.json
   output_path: digests/latest.md
   ```

3. Test it once:

   ```bash
   python3 run.py --config config.yaml --print
   ```

4. Add to crontab (every 4 hours) with `crontab -e`:

   ```cron
   0 */4 * * * cd /path/to/deal-hunter && /usr/bin/python3 run.py --config config.yaml >> run.log 2>&1
   ```

`state/seen.json` persists on the same machine between runs, so you never get
duplicate alerts. Read the latest digest at `digests/latest.md`, or have cron
email it / push it to a chat.

## B) Cloud Routine (Claude Code on the web)

A scheduled cloud agent can run this every few hours **if the environment's
network policy allows outbound access to your target site**. The default
"no-egress" policy blocks classifieds/reddit, so choose an environment with a
wider network policy first (see the Claude Code on the web docs on network
policies). Then the Routine each run should:

1. `git pull` this repo,
2. `python3 deal-hunter/run.py --config deal-hunter/config.yaml`,
3. commit the updated `deal-hunter/state/seen.json` and
   `deal-hunter/digests/latest.md` back (so memory survives the ephemeral
   container),
4. report the top new deals in its summary / a push notification.

Because the container is wiped between runs, committing the state file is what
gives the cloud Routine a memory. On a machine with cron (option A) the local
filesystem already provides that.

## Notes

- Keep polling gentle and prefer official feeds/APIs; respect each site's terms.
- The agent only reports. It never buys, sells, or messages anyone.
