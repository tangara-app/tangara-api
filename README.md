# Tangara — AI video generation API & MCP

Generate videos with LTX-2.5 through [Tangara](https://tangara.app), from your
application or an AI assistant. Start with a text prompt, optionally add a first
and last frame, check the price, and download the completed MP4.

[Open the studio](https://tangara.app) · [API documentation](https://docs.tangara.app)

This repository contains client examples. Inference runs on Tangara; no local GPU
or model download is required to use the API.

## Capabilities

| Capability | Interface |
| --- | --- |
| Text-to-video and image-to-video with LTX-2.5 | REST and MCP |
| Landscape, portrait and square video | Select an exact profile from the catalog |
| Resolutions from 480p to 4K | Check available profiles and duration limits |
| Generated video audio | The `audio` option |
| Image creation and reference editing with FLUX.2 Klein | Media API and MCP |
| Music with ACE-Step; speech with Chatterbox | Media API and MCP |
| Quotes, balance and private generation history | REST and MCP |

The live catalog is authoritative for availability, dimensions, limits and prices.
See the full documentation for media generation and additional input modes.

## Get started

1. Sign in to Tangara and open **Account → API key**.
2. Copy `.env.example` to `.env` and enter your personal Tangara API key.
3. Load the variables in your shell: `set -a; . ./.env; set +a`.

Keep the key on your server or computer, outside browser code and Git.
Python examples use Python 3.10+ and the standard library. JavaScript examples
use Node.js 22+ and require no packages.

## Generate a video

The examples use three explicit steps. Preparing a request fetches its price but
does not generate a video or spend your balance. Submitting queues paid work.

| Step | Python | JavaScript |
| --- | --- | --- |
| Show models and available profiles | `python3 examples/video.py models` | `node examples/video.mjs models` |
| Save a request and show its quoted price | `python3 examples/video.py prepare request.json` | `node examples/video.mjs prepare request.json` |
| Submit the saved request | `python3 examples/video.py submit request.json` | `node examples/video.mjs submit request.json` |
| Wait for a task and get its result links | `python3 examples/video.py wait TASK_UUID` | `node examples/video.mjs wait TASK_UUID` |

Set `TANGARA_PROMPT`, `TANGARA_PROFILE_ID` and `TANGARA_DURATION_SECONDS` before
preparing a request. The default is a five-second 720p landscape video with audio.
The request file contains the immutable accepted quote and a unique request ID.
Preparing never overwrites an existing file.

If submission times out, submit **the same file again**. Tangara returns the same
task rather than creating and charging for a second one. Keep the same account,
API endpoint and request body. For a different video, prepare a new file.

If Tangara returns `price_changed`, review a fresh quote before creating a new
request. An insufficient balance returns `insufficient_funds`. A polling timeout
does not cancel a task: repeat `wait` with the same task ID.

The result includes a temporary `download_url` and an account-only `video_url`.
Run `wait` again to refresh an expired download URL. Download the MP4 from the
signed URL without forwarding your Tangara API key to object storage.

## Image-to-video

Upload a first frame with your API key. Save the returned asset `id`:

```sh
curl --fail-with-body --silent --show-error \
  "$TANGARA_API_URL/assets" \
  -H "Authorization: Bearer $TANGARA_API_KEY" \
  -F 'file=@first-frame.png'
```

Set `TANGARA_FIRST_IMAGE_ID` to that ID, then prepare a new request using either
example. For an end frame, upload a second image and also set
`TANGARA_LAST_IMAGE_ID`. An end frame requires a first frame. Input images must
belong to your account. PNG, JPEG and WebP are supported; see the documentation
for current upload limits. Keep the returned ID instead of uploading repeatedly.

## MCP: generate from an AI assistant

Connect a client supporting Streamable HTTP and a custom authorization header:

```text
URL: https://tangara.app/mcp
Authorization: Bearer YOUR_TANGARA_API_KEY
```

Use `list_models` → `quote_video` → `generate_video` → `get_video` →
`get_video_result`. Accept the quote before generation. Pass its `version` and
`amount` as `expected_price`, and retain `client_request_id` on retries.
Discover the available media tools through the same MCP connection.

REST, MCP and the studio share your account, balance, prices and private history.

## Pricing and task status

Amounts are integer strings in thousandths of USD (`scale: 1000`), not dollars.
The examples display the returned quote instead of hard-coding a tariff.
Generation charges the balance when the task enters the queue. A final generation
failure refunds the Tangara balance. Card refunds are handled manually.

Task results are `in_progress`, `succeeded` or `failed`. The separate `stage`
field distinguishes queueing, preparation, generation and uploading. Submission
does not mean the MP4 is immediately ready.

## Support

[Documentation](https://docs.tangara.app) · [Tangara](https://tangara.app) ·
[Support](mailto:support@tangara.app)

Tangara provides the hosted service. LTX, FLUX, ACE-Step and Chatterbox are models
from their respective developers. This repository does not contain model weights.
