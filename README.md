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
