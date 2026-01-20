##   
##   starikcetin
##   cetinsamedtarik@gmail.com
##   github.com/starikcetin
##

try:
    import sys
    import os

    # Automatically detect the script directory (like the shell script does)
    script_dir = os.path.dirname(os.path.abspath(__file__))

    def read_file(path):
        print("Reading file: " + path)
        with open(path, 'r') as content_file:
            content = content_file.read()
            return content


    def write_file(path, content):
        print(path)
        if os.path.exists(path):
            with open(path, 'r') as f:
                if content in f.read():
                    print("Skipping (the file already has the hooks).")
                    return

        with open(path, "a+") as f:
            print("Appending.")
            f.write(str(content))
        
        # On Unix systems, make the hook executable
        if os.name != 'nt':  # Not Windows
            os.chmod(path, 0o755)


    print("This script will either create or append the hooks to your repository.")
    print("It will search within the files before appending to prevent duplication.")
    print()
    print("This installer is written by github.com/starikcetin")
    print("Enjoy!")
    print()
    print()

    repo_root_folder = input("Enter path of the repository root: ")
    #print("repo root:\t" + repo_root_folder)
    assert os.path.exists(repo_root_folder), "This folder does not exist: " + str(repo_root_folder)

    dot_git_folder = os.path.join(repo_root_folder, ".git/")
    #print(".git folder:\t" + dot_git_folder)
    assert os.path.exists(dot_git_folder), "This folder is not the root of a git repository: " + str(repo_root_folder)
    print()
    print()

    print("Reading hooks...")
    print()
    post_checkout_commands = read_file(os.path.join(script_dir, "post-checkout"))
    post_merge_commands = read_file(os.path.join(script_dir, "post-merge"))
    pre_commit_commands = read_file(os.path.join(script_dir, "pre-commit"))
    print()
    print()

    print("Writing hooks...")
    print()
    print("post-checkout")
    write_file(os.path.join(dot_git_folder, "hooks/", "post-checkout"), post_checkout_commands)
    print()
    print("post-merge")
    write_file(os.path.join(dot_git_folder, "hooks/", "post-merge"), post_merge_commands)
    print()
    print("pre-commit")
    write_file(os.path.join(dot_git_folder, "hooks/", "pre-commit"), pre_commit_commands)
    print()
    print()

    print("Done.")

except Exception as ex:
    print()
    print("Error occurred: " + str(ex))
        
input("Press any key to exit.")
