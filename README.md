1.  **Deconstruct the User's Request:** The user wants a "readme for github" for the provided Python script, `organize_by_handle.py`. This is a clear and direct request.

2.  **Initial Analysis & Goal Setting:**
    *   **Audience:** Who is this for? Other developers, or maybe even non-technical users who have a folder of images they want to organize (e.g., photographers, social media managers). The tone should be clear, informative, and accessible.
    *   **Purpose:** The README needs to explain what the script does, why someone would use it, and *how* to use it. It should be a comprehensive guide.
    *   **Key Information to Extract from the Script:**
        *   Core purpose: Organizing image files into subfolders based on Instagram-like handles in the filenames.
        *   Key features: Prefers handles at the start, preserves original casing and leading characters (`_`, `.`), trims date/numeric tails, has fallbacks, is move-only, has a dry-run mode, logs to CSV, has configurable options (min files, extensions, etc.).
        *   Dependencies: It's a Python 3 script. It uses standard libraries (`argparse`, `re`, `shutil`, `csv`, `pathlib`), so no external `pip install` is needed. This is important to mention.
        *   Usage: It's a command-line tool. I need to document all the `argparse` arguments.

3.  **Consult Best Practices (Internal Knowledge & Search Strategy):**
    *   I have a strong internal model of what a good README contains. It's a standard format.
    *   I initiated a Google Search for `how to write a good github readme` to refresh and validate this internal model. This search confirms the standard sections:
        *   **Title:** Clear and descriptive.
        *   **Description/Introduction:** A concise summary of the "what" and "why."
        *   **Badges:** (Optional but good for mature projects) e.g., build status, version. I'll skip this for a single script, as it's overkill.
        *   **Visuals:** Screenshots or GIFs are highly effective. I can't generate a real GIF, but I can *simulate* the "before and after" using a code block, which is the next best thing.
        *   **Features:** A bulleted list of key capabilities. This is crucial for quickly scanning what the tool can do.
        *   **Installation/Requirements:** How to get the script ready to run.
        *   **Usage:** Detailed explanation of the command-line arguments and examples. This is the most critical part for a CLI tool.
        *   **How it Works/Heuristics:** A deeper dive into the logic. For this script, the handle detection logic is the "secret sauce," so explaining it is important for users to understand *why* a file was grouped (or not grouped).
        *   **Contributing:** (Optional but good practice). I'll add a simple section.
        *   **License:** Important for any open-source project. I'll suggest adding one.

4.  **Structuring the README.md:** I'll create a skeleton based on the best practices identified above.

    *   `# Title`
    *   `> Short Description`
    *   `## Key Features`
    *   `## Before & After` (The visual demo)
    *   `## Requirements`
    *   `## How to Use`
        *   `### Basic Usage`
        *   `### Command-Line Arguments`
    *   `## How it Works: Handle Detection Logic` (Explaining the heuristics)
    *   `## Logging`
    *   `## Contributing`
    *   `## License`

5.  **Drafting the Content (Section by Section):**

    *   **Title:** "Organize by Handle" is simple and accurate.
    *   **Description:** I'll take the docstring from the top of the Python file and rephrase it slightly to be more user-facing. The core idea is "organize a flat folder of images into subfolders by Instagram-like handles."
    *   **Key Features:** I'll go through the script's docstring, comments, and argument parser to pull out the most important features.
        *   Preserves exact handle form (casing, leading `_`/`.`).
        *   Prefers handles at the *start* of the filename.
        *   Smartly trims date/numeric tails.
        *   No external dependencies.
        *   `--dry-run` for safety.
        *   CSV logging.
        *   Configurable (`--min-count`, `--ext`, etc.).
        *   Fallback heuristics (`@` anywhere, trailing handles).
    *   **Before & After:** This is where I'll create the simulated demo. I'll invent some realistic filenames that showcase the script's logic (`handle_blah.jpg`, `__handle.with.dots_20250905.png`, `IMG_1234.jpg`, etc.) and show the resulting folder structure. This makes the script's purpose immediately obvious.
    *   **Requirements:** Simple. "Python 3." Mention that no external packages are needed.
    *   **How to Use:**
        *   First, explain how to download/get the script (`git clone` or just download the `.py` file).
        *   Then, provide a simple, common-sense example: `python organize_by_handle.py /path/to/your/images`.
        *   Follow up with a more complex example showing multiple flags (`--dry-run`, `--min-count=1`, `--log`).
        *   Create a detailed breakdown of every command-line argument from the `argparse` section of the script. I'll use Markdown's code formatting (`--argument`) and blockquotes or lists to explain what each one does.
    *   **Handle Detection Logic:** This is the most technical part of the README. I'll break down the `infer_handle` and `take_leading_handle_token_preserve` logic into a step-by-step process, mirroring the comments in the code. This builds user trust and helps them understand the results. I'll cover the primary (strict start) logic first, then the fallbacks.
    *   **Logging:** Since the script has a dedicated `--log` feature, it deserves its own small section explaining the format of the CSV file.
    *   **Contributing & License:** These are standard boilerplate sections. I'll add placeholder text encouraging pull requests and reminding the user to add a `LICENSE` file.

6.  **Review and Refine:** I'll read through the entire generated Markdown file. Is it clear? Is the formatting correct (code blocks, headings, lists)? Is the tone helpful? Is anything missing? The goal is to anticipate user questions and answer them proactively. The "Before & After" section is particularly powerful and should be placed early to grab attention. The detailed argument list is essential for usability.

This systematic process ensures all aspects of the script are documented in a way that follows established best practices for GitHub projects, making it easy for users to understand, use, and trust the tool.Of course. Here is a comprehensive README.md file for the provided Python script. It is structured to be clear, informative, and user-friendly, following best practices for GitHub projects.

---

# Organize by Handle

A Python command-line script to organize a flat folder of images into subfolders named after inferred Instagram-like handles from the filenames. It intelligently finds handles, preserves their original format, and moves the files into corresponding directories.

This is ideal for cleaning up downloaded image collections where the original creator's handle is part of the filename.

## Key Features

*   **Preserves Exact Handles**: Unlike other tools, this script keeps the original casing and leading characters (e.g., `__my.handle_` becomes a folder named `__my.handle_`).
*   **Prefers Leading Handles**: The script prioritizes handles found at the very beginning of a filename, which is the most common convention.
*   **Smart Name Cleaning**: Automatically trims common numeric or date-based tails from filenames (e.g., `handle_2025-08-23.jpg` correctly identifies `handle`).
*   **Safe Execution**: Use the `--dry-run` flag to see what changes will be made without moving a single file.
*   **No External Dependencies**: Runs using only standard Python 3 libraries. No `pip install` required.
*   **Flexible Heuristics**: Includes fallback options to find handles preceded by an `@` symbol or located at the end of the filename.
*   **Comprehensive Logging**: Optionally creates a CSV log of all file operations for tracking and review.
*   **Highly Configurable**: Adjust the minimum number of files per handle, specify allowed extensions, and control the strictness of the detection logic.

## How It Works: Before & After

Imagine you have a messy folder like this:

```
 messy_downloads/
 ├── __cool_user_.12345.jpg
 ├── __cool_user_.67890.png
 ├── another-user-2025-09-01.jpeg
 ├── IMG_4321.jpg
 ├── just.a.handle.webp
 ├── photo_by_@some_artist.png
 ├── PXL_20250905_123456.jpg
 ├── some_artist_edit.jpg
 └── unrelated_file.txt
```

After running the script:

`python organize_by_handle.py ./messy_downloads --min-count 1`

You get a clean, organized structure:

```
 messy_downloads/
 ├── __cool_user_/
 │   ├── __cool_user_.12345.jpg
 │   └── __cool_user_.67890.png
 │
 ├── another-user/
 │   └── another-user-2025-09-01.jpeg
 │
 ├── just.a.handle/
 │   └── just.a.handle.webp
 │
 ├── some_artist/
 │   ├── photo_by_@some_artist.png
 │   └── some_artist_edit.jpg
 │
 ├── IMG_4321.jpg
 ├── PXL_20250905_123456.jpg
 └── unrelated_file.txt```

Files that don't have a recognized handle (like camera-named files) are left untouched in the root folder.

## Requirements

*   Python 3.x

That's it! The script uses only built-in Python libraries.

## How to Use

1.  Download the `organize_by_handle.py` script to your computer.
2.  Open your terminal or command prompt.
3.  Navigate to the directory where you saved the script or use its full path.

#### Basic Usage

To run the script on a folder, provide the folder's path as the main argument. By default, it will only create folders for handles that appear on 3 or more files.

```bash
python organize_by_handle.py "/path/to/your/image folder"
```

#### Dry Run (Recommended First)

Preview all planned moves without touching any files. This is the safest way to start.

```bash
python organize_by_handle.py "/path/to/your/images" --dry-run
```

#### Organizing All Handles (including single files)

To create a folder for every single file that has a valid handle, use `--include-singletons` or set `--min-count 1`.

```bash
python organize_by_handle.py "/path/to/your/images" --include-singletons
```

### Command-Line Arguments

Here is a full list of available options:

| Argument                 | Description                                                                                                                              | Default                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------- |
| `folder`                 | **(Required)** The path to the folder of images you want to organize. The script does not recurse into subdirectories.                     | -                                             |
| `--min-count`            | The minimum number of files needed for a handle to get its own folder.                                                                   | `3`                                           |
| `--include-singletons`   | A shortcut for `--min-count 1`. If present, it organizes files even if their handle is unique.                                           | `False`                                       |
| `--dry-run`              | A crucial safety feature. It prints all the actions it *would* take without actually moving any files.                                   | `False`                                       |
| `--ext`                  | A space-separated list of allowed file extensions to scan.                                                                               | `jpg jpeg png webp heic`                      |
| `--log`                  | The path to a CSV file where all move operations will be logged. The file and its parent directories will be created if they don't exist. | `None`                                        |
| `--strict-start`         | Enforces that a handle must be found at the very beginning of the filename. Disables fallback heuristics.                                | `False`                                       |
| `--no-trailing`          | Disables the fallback heuristic that looks for a handle at the very end of the filename (before the date/numeric tail).                   | `False` (meaning the heuristic is **enabled**) |

## Handle Detection Logic

The script uses a series of heuristics to find the most likely handle in a filename.

#### 1. Primary Method: Leading Handle (Preserved)

This is the main and preferred method. It works as follows:
1.  Looks at the very **start** of the filename (e.g., `__handle.123_...`).
2.  Preserves leading underscores (`_`) and dots (`.`).
3.  Preserves the original letter casing (e.g., `Handle` is different from `handle`).
4.  Stops at the first "hard" separator (like a space, `-`, `(`, etc.).
5.  Trims off any trailing date or long number sequences (e.g., `my_handle_20250905` becomes `my_handle`).
6.  Validates the result: must be 3-30 characters, contain at least one letter, and not be a generic camera prefix (like `IMG`, `PXL`, `DSC`, etc.).

#### 2. Fallback Methods

If no handle is found at the start of the name and `--strict-start` is **not** used, the script will try these fallbacks:

*   **`@` Symbol Anywhere**: It looks for a valid handle directly following an `@` symbol anywhere in the filename.
*   **Trailing Handle**: As a last resort (if `--no-trailing` is not used), it looks at the very end of the filename stem for something that looks like a handle.

## Logging

If you use the `--log <path/to/log.csv>` argument, the script will generate a CSV file with the following columns:

*   **action**: The action taken (`MOVED` or `DRY-RUN-MOVE`).
*   **handle**: The handle that was inferred for the file.
*   **src**: The original, full path of the source file.
*   **dst**: The final, full path of the destination file.

This log is useful for auditing the script's actions or for scripting reversals if needed.

## Contributing

Feel free to fork the repository, make improvements, and submit a pull request. If you find a bug or have a suggestion, please open an issue.

## License

This project is open-source. Please add a `LICENSE` file (e.g., MIT, GPL) if you intend to distribute it more widely.
