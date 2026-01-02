# 🌍 Translations Guide

Smart Room Manager supports multiple languages through Home Assistant's translation system.

## Available Languages

- **English** (en) - Default language
- **Français** (fr) - French translation

## How Translations Work

Home Assistant uses a two-file system for translations:

1. **`strings.json`** - Default language (English)
   - Located in: `custom_components/smart_room_manager/strings.json`
   - Used when no translation is available for user's language

2. **`translations/{lang}.json`** - Language-specific translations
   - Located in: `custom_components/smart_room_manager/translations/`
   - One file per language (e.g., `fr.json`, `de.json`, `es.json`)

Home Assistant automatically selects the correct translation based on the user's language setting.

## File Structure

Both `strings.json` and `translations/{lang}.json` must have the same structure:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "...",
        "description": "...",
        "data": {
          "field_name": "..."
        }
      }
    }
  },
  "options": {
    "step": {
      "step_name": {
        "title": "...",
        "description": "...",
        "data": {
          "field_name": "..."
        }
      }
    }
  }
}
```

## Adding a New Language

To add support for a new language (e.g., German):

### 1. Create Translation File

Create `custom_components/smart_room_manager/translations/de.json`:

```bash
cd custom_components/smart_room_manager/translations
cp en.json de.json
```

### 2. Translate Content

Edit `de.json` and translate all strings to German:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "Smart Room Manager konfigurieren",
        "description": "Vereinfachte Konfiguration v0.2.0 - Alarm bestimmt Anwesenheit, keine Anwesenheits-/Helligkeitssensoren",
        "data": {
          "alarm_entity": "Alarm-Entität",
          "season_calendar": "Saison-Kalender"
        }
      }
    }
  },
  "options": {
    ...
  }
}
```

### 3. Validate JSON

Ensure your translation file is valid JSON:

```bash
python -c "import json; json.load(open('custom_components/smart_room_manager/translations/de.json'))"
```

If no error appears, the JSON is valid.

### 4. Test Translation

1. Restart Home Assistant
2. Go to **Settings → System → General**
3. Change language to German
4. Navigate to **Settings → Integrations → Smart Room Manager**
5. Verify that UI text appears in German

## Translation Keys Reference

### Config Flow Steps

| Step | Purpose |
|------|---------|
| `user` | Initial configuration (alarm, season calendar) |

### Options Flow Steps

| Step | Purpose |
|------|---------|
| `init` | Main menu |
| `list_rooms` | List all configured rooms |
| `add_room` | Add new room - basic info |
| `edit_room_basic` | Edit room basic info |
| `room_sensors` | Configure sensors |
| `room_actuators` | Configure actuators (lights, climate) |
| `room_light_config` | Configure light behavior |
| `room_climate_config` | Configure climate temperatures |
| `room_climate_advanced` | Advanced climate (hysteresis, presets) |
| `room_schedule` | Configure schedule and calendar |
| `room_control` | Configure manual pause options |
| `delete_room` | Confirm room deletion |
| `global_settings` | Global settings (alarm, season calendar) |

### Common Fields

| Field | Used In | Description |
|-------|---------|-------------|
| `alarm_entity` | config, global_settings | Alarm control panel entity |
| `season_calendar` | config, global_settings | Calendar for summer/winter detection |
| `room_name` | add_room, edit_room_basic | Name of the room |
| `room_type` | add_room, edit_room_basic | Room type (normal, corridor, bathroom) |
| `room_icon` | add_room, edit_room_basic | Icon for the room |
| `lights` | room_actuators | Light entities |
| `climate_entity` | room_actuators | Climate entity |
| `temperature_sensor` | room_sensors | Temperature sensor |
| `temp_comfort` | room_climate_config | Comfort temperature (winter) |
| `temp_eco` | room_climate_config | Eco temperature (winter) |
| `temp_night` | room_climate_config | Night temperature (winter) |
| `night_start` | room_schedule | Night start time |
| `pause_duration_minutes` | room_control | Pause duration |

## Placeholders

Some strings contain placeholders that are replaced at runtime:

- `{room_name}` - Replaced with actual room name
- `{room_type}` - Replaced with actual room type

**Example:**
```json
"description": "Configure sensors for {room_name}"
```

Becomes: "Configure sensors for Living Room"

## Translation Guidelines

### 1. Consistency

Use consistent terminology throughout:
- "Room" → always use the same word
- "Temperature" → always use the same word
- "Sensor" → always use the same word

### 2. Context

Consider the context when translating:
- UI labels should be short and clear
- Descriptions can be longer and more detailed
- Error messages should be informative

### 3. Technical Terms

Some terms may be better left in English or transliterated:
- "Home Assistant" - brand name, don't translate
- "YAML" - technical term, don't translate
- "X4FP" - product name, don't translate
- "Solar Optimizer" - may vary by language/region

### 4. Units

Include units where appropriate:
- Temperatures: "°C" or "°F" depending on region
- Time: "seconds", "minutes", "hours"
- Distances: "meters", "feet"

### 5. Formality

Match the formality level of Home Assistant:
- Use "you" (informal/formal depending on language)
- Be helpful and friendly
- Avoid technical jargon unless necessary

## Language Codes

Use ISO 639-1 two-letter language codes:

| Code | Language |
|------|----------|
| `en` | English |
| `fr` | Français (French) |
| `de` | Deutsch (German) |
| `es` | Español (Spanish) |
| `it` | Italiano (Italian) |
| `nl` | Nederlands (Dutch) |
| `pt` | Português (Portuguese) |
| `ru` | Русский (Russian) |
| `zh` | 中文 (Chinese) |
| `ja` | 日本語 (Japanese) |
| `ko` | 한국어 (Korean) |

## Contributing Translations

To contribute a new translation:

1. **Fork** the repository
2. **Create** translation file in `custom_components/smart_room_manager/translations/{lang}.json`
3. **Translate** all strings
4. **Validate** JSON syntax
5. **Test** in Home Assistant
6. **Submit** pull request

### Pull Request Guidelines

When submitting a translation:

- Title: `feat: Add {language} translation`
- Description: Include:
  - Language name and code
  - Native speaker confirmation (if possible)
  - Testing confirmation
  - Any regional variations or notes

### Example PR Description

```markdown
## Add German Translation

- Language: Deutsch (German)
- Code: `de`
- Translator: Native German speaker
- Tested: ✅ Home Assistant 2024.1
- Notes: Used formal "Sie" form for consistency with HA
```

## Maintenance

When updating the integration:

1. **Update `strings.json`** with new keys
2. **Update `translations/en.json`** (copy from strings.json)
3. **Update all other language files** with new keys
4. **Test** each language

### Version Compatibility

Translations are version-specific:
- v0.2.0: Simplified config flow
- v0.3.0: Added advanced climate, external control, schedule
- v0.3.1+: Current structure

When upgrading from older versions, ensure translation files match the current `strings.json` structure.

## Troubleshooting

### Translation Not Showing

1. **Check file location**: Must be in `translations/{lang}.json`
2. **Check language code**: Must match user's language setting
3. **Restart Home Assistant**: Required after translation changes
4. **Clear browser cache**: May cache old translations

### Missing Translations

If some text appears in English even with a translation file:

1. **Check JSON structure**: Must match `strings.json` exactly
2. **Check for typos**: Field names must match exactly
3. **Check for missing keys**: All keys in `strings.json` must be in translation

### Invalid JSON

```bash
# Validate JSON syntax
python -c "import json; json.load(open('translations/de.json'))"

# Pretty-print JSON (helps find errors)
python -m json.tool translations/de.json
```

## Resources

- [Home Assistant Translations](https://developers.home-assistant.io/docs/internationalization/)
- [JSON Validator](https://jsonlint.com/)
- [ISO 639-1 Language Codes](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes)

## Current Translation Status

| Language | Status | Translator | Last Updated |
|----------|--------|------------|--------------|
| English (en) | ✅ Complete | Built-in | v0.3.2 |
| Français (fr) | ✅ Complete | Built-in | v0.3.2 |
| Deutsch (de) | ❌ Missing | - | - |
| Español (es) | ❌ Missing | - | - |
| Italiano (it) | ❌ Missing | - | - |

**Want to help?** Submit a translation! See [Contributing Translations](#contributing-translations) above.

---

Need help with translations? Open an issue on GitHub!
