from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()

client = AsyncOpenAI(
    base_url=settings.DTGPT_BASE_URL,
    api_key=settings.DTGPT_API_KEY,
)

SYSTEM_PROMPT = """You are a test case code generator for Android device testing.
You ONLY generate Python test case code using the test_executor_sdk library.
If the user asks anything unrelated to test case generation, politely decline and say:
"저는 테스트 케이스 생성 봇입니다. 테스트 케이스 생성과 관련된 요청만 처리할 수 있습니다."

## test_executor_sdk API Reference

### Imports
```python
from test_executor_sdk import TestCase, device, step, assert_screen
```

### TestCase Base Class
- Inherit from `TestCase`
- Set `app_package` (str): target app package name
- Set `timeout_per_step` (int): per-step timeout in seconds (default 30)
- Define steps as methods decorated with `@step("step description")`
- Methods should be named `step_XX_name` with incrementing numbers

### Device Control
| API | Description |
|-----|-------------|
| `device.launch_app(package)` | Launch app |
| `device.stop_app(package)` | Stop app |
| `device.tap(text=, resource_id=, xy=)` | Tap element |
| `device.long_tap(text=, resource_id=, xy=, duration=)` | Long tap |
| `device.swipe(start_xy, end_xy, duration=)` | Swipe |
| `device.swipe_direction(direction, duration=)` | Direction swipe (up/down/left/right) |
| `device.input_text(text)` | Input text |
| `device.press_key(key)` | Key press (back, home, enter, volume_up, etc.) |
| `device.wait(seconds)` | Wait |

### UI Exploration
| API | Description |
|-----|-------------|
| `device.find_element(text=, resource_id=, class_name=)` | Find UI element |
| `device.get_ui_tree()` | Get full UI tree |
| `device.wait_for_element(text=, resource_id=, timeout=)` | Wait for element |
| `device.element_exists(text=, resource_id=)` | Check element exists |

### Assertions
| API | Description |
|-----|-------------|
| `assert_screen(text_exists=)` | Assert text exists on screen |
| `assert_screen(text_not_exists=)` | Assert text not on screen |
| `assert_screen(resource_id_exists=)` | Assert resource ID exists |
| `assert_element(text=, attribute=, expected=)` | Assert element attribute |

### Data Collection
| API | Description |
|-----|-------------|
| `device.screenshot(name)` | Take screenshot |
| `device.get_logcat(filter=, lines=)` | Collect logcat |
| `device.get_current_activity()` | Get current activity |
| `device.get_device_info()` | Get device info |

## Output Format
Always output ONLY the Python code. No markdown fences, no explanations before/after the code.
Use Korean for step descriptions and docstrings.
"""


def _is_tc_request(message: str) -> bool:
    tc_keywords = [
        "테스트", "test", "tc", "TC", "케이스", "case", "스크립트", "script",
        "만들어", "생성", "작성", "create", "generate", "write",
        "시나리오", "scenario", "자동화", "automation",
    ]
    message_lower = message.lower()
    return any(kw.lower() in message_lower for kw in tc_keywords)


async def generate_tc_code(
    user_message: str,
    file_content: str | None = None,
    conversation_history: list[dict] | None = None,
) -> tuple[str, str | None]:
    """Generate TC code from user message. Returns (reply_text, code_or_none)."""

    if not _is_tc_request(user_message):
        return (
            "저는 테스트 케이스 생성 봇입니다. 테스트 케이스 생성과 관련된 요청만 처리할 수 있습니다.",
            None,
        )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if conversation_history:
        messages.extend(conversation_history)

    user_content = user_message
    if file_content:
        user_content += f"\n\n--- 첨부 문서 내용 ---\n{file_content}"

    messages.append({"role": "user", "content": user_content})

    response = await client.chat.completions.create(
        model=settings.DTGPT_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=4096,
    )

    reply = response.choices[0].message.content or ""

    # Extract code: the model is instructed to output only code,
    # but strip markdown fences if present
    code = reply.strip()
    if code.startswith("```python"):
        code = code[len("```python"):].strip()
    if code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()

    return reply, code
