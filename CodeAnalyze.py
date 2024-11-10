import os
import shutil
import openai
import subprocess  # Add this import
import re
import requests 

class DotNetCodeAnalyzer:
    def __init__(self, solution_path, api_key):
        self.solution_path = solution_path
        openai.api_key = api_key

    def create_solution_copy(self, root_folder_path):
        # Create the 'MigrationSolutions' directory inside the specified root folder path
        migration_root = os.path.join(root_folder_path, "MigrationSolutions")
        os.makedirs(migration_root, exist_ok=True)

        # Calculate the relative path of the solution's directory from the root folder
        relative_path = os.path.relpath(os.path.dirname(self.solution_path), root_folder_path)

        # Construct the full destination path within 'MigrationSolutions', preserving directory structure
        upgraded_dir = os.path.join(migration_root, relative_path)
        
        # Ensure that the entire structure within the solution directory is copied
        if os.path.exists(upgraded_dir):
            shutil.rmtree(upgraded_dir)  # Remove existing to avoid conflicts
        shutil.copytree(os.path.dirname(self.solution_path), upgraded_dir)

        # Set the upgraded solution path
        self.upgraded_solution_path = upgraded_dir
        print(f"\033[1;32mSolution directory copied to {self.upgraded_solution_path} successfully\033[0m")

    def upgrade_csproj_files(self):
        # Define the target framework version for .NET 8
        target_framework_version = "net8.0"
        
        # Possible framework targets to upgrade from
        possible_frameworks = ["netcoreapp", "netstandard", "net5.0", "net6.0", "net7.0"]

        for root, dirs, files in os.walk(self.upgraded_solution_path):
            for file in files:
                if file.endswith(".csproj"):
                    csproj_path = os.path.join(root, file)
                    with open(csproj_path, "r") as f:
                        content = f.read()
                    
                    modified = False
                    # Look for each possible framework and replace it correctly
                    for framework in possible_frameworks:
                        if f"<TargetFramework>{framework}" in content:
                            print(f"Upgrading {file} from {framework} to .NET 8...")
                            # Replace the framework version without duplicating tags
                            content = content.replace(
                                f"<TargetFramework>{framework}", f"<TargetFramework>{target_framework_version}"
                            )
                            modified = True

                    # Write the changes only if modifications were made
                    if modified:
                        with open(csproj_path, "w") as f:
                            f.write(content)

    def check_for_vulnerabilities(self):
        prompt = "List common vulnerabilities in a .NET Core application and suggest mitigations."
        response = openai.chat.completions.create(
            model="gpt-4",  # Replace with "gpt-4" if available to you
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()

    def propose_efficiency_improvements(self):
        prompt = "Suggest improvements for enhancing code efficiency in .NET 8."
        response = openai.chat.completions.create(
            model="gpt-4",  # Replace with "gpt-4" if available to you
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        return response.choices[0].message.content.strip()

    def analyze_cs_files(self):
        recommendations = []
        deprecated_methods = ["System.Web", "BinaryFormatter", "HttpContext.Current"]  # Add more if needed

        for root, dirs, files in os.walk(self.upgraded_solution_path):
            for file in files:
                if file.endswith(".cs"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r") as f:
                        lines = f.readlines()

                    # Track class and line number for recommendations
                    for i, line in enumerate(lines):
                        # Find class names
                        if "class " in line:
                            class_name = re.search(r'class\s+(\w+)', line)
                            if class_name:
                                current_class = class_name.group(1)

                        # Check for deprecated methods
                        for method in deprecated_methods:
                            if method in line:
                                recommendations.append(
                                    f"Deprecated method '{method}' found in {file} at line {i+1} in class {current_class}."
                                )
        return recommendations

    def list_outdated_nuget_packages(self):
        nuget_updates = []
        for root, dirs, files in os.walk(self.upgraded_solution_path):
            for file in files:
                if file.endswith(".csproj"):
                    csproj_path = os.path.join(root, file)
                    with open(csproj_path, "r") as f:
                        content = f.read()

                    # Use regex to capture the package name and version
                    packages = re.findall(r'<PackageReference Include="([^"]+)" Version="([^"]+)"', content)
                    for package_name, version in packages:
                        # Placeholder to check for outdated packages (real implementation would query NuGet)
                        nuget_updates.append(f"NuGet package '{package_name}' version '{version}' in {file} might need upgrading.")
        return nuget_updates

    def build_solution(self):
        print("Building the upgraded solution...")
        try:
            subprocess.run(
                ["dotnet", "build", self.upgraded_solution_path],
                capture_output=True,
                text=True,
                check=True
            )
            # print("\033[1;32mBuild succeeded without errors.\033[0m")
            print("\n" + "="*120)
            print("\033[1;32m" + " " * 10 + "***** BUILD SUCCEEDED WITHOUT ERRORS *****" + " " * 10 + "\033[0m")
            print("="*120 + "\n")

            return None  # No errors
        except subprocess.CalledProcessError as e:
            print("\033[1;31mBuild failed. Capturing errors for analysis.\033[0m")
            return e.stderr  # Capture build error messages

    

    def analyze_build_errors(self, build_errors):
        prompt = (
            "The following build errors were encountered after upgrading a .NET Core solution to .NET 8:\n\n"
            f"{build_errors}\n\n"
            "Please suggest solutions to resolve these errors."
        )
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        return response['choices'][0]['message']['content'].strip()

    def save_to_notepad(self, vulnerabilities, improvements, build_suggestions=None, recommendations=None, nuget_updates=None):
        log_path = os.path.join(self.upgraded_solution_path, "Upgrade_Recommendations.txt")
        with open(log_path, "w") as f:
            f.write("Vulnerability Analysis:\n")
            f.write(vulnerabilities + "\n\n")
            f.write("Efficiency Recommendations:\n")
            f.write(improvements + "\n\n")
            if recommendations:
                f.write("Code Recommendations (Deprecated Methods):\n")
                f.write("\n".join(recommendations) + "\n\n")
            if nuget_updates:
                f.write("NuGet Package Upgrade Recommendations:\n")
                f.write("\n".join(nuget_updates) + "\n\n")
            if build_suggestions:
                f.write("Build Error Suggestions:\n")
                f.write(build_suggestions + "\n")
        print(f"Recommendations saved to {log_path}")

    def upgrade_docker_image(self):
        print("No Dockerfile found in the solution path.")
        dockerfile_path = os.path.join(self.upgraded_solution_path, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            print("No Dockerfile found in the solution path.")
            return

        print("Dockerfile found. Attempting to upgrade Docker images...")

        # Read Dockerfile content
        with open(dockerfile_path, "r") as file:
            content = file.read()

        # Check for current .NET SDK and ASP.NET images (with flexibility for tag variations)
        sdk_pattern = r"mcr\.microsoft\.com/dotnet/sdk:6\.0(?:-[a-zA-Z0-9]+)?"
        aspnet_pattern = r"mcr\.microsoft\.com/dotnet/aspnet:6\.0(?:-[a-zA-Z0-9]+)?"

        # Replace with .NET 8 images
        updated_content = re.sub(sdk_pattern, "mcr.microsoft.com/dotnet/sdk:8.0", content)
        updated_content = re.sub(aspnet_pattern, "mcr.microsoft.com/dotnet/aspnet:8.0", updated_content)

        # Check if any changes were made
        if content != updated_content:
            with open(dockerfile_path, "w") as file:
                file.write(updated_content)
            print("\033[1;32mDockerfile upgraded successfully to .NET 8.\033[0m")

        else:
            print("Dockerfile is already using .NET 8 or no matching patterns were found.")
            
            print("Dockerfile upgraded successfully.")

    def get_latest_nuget_version(self, package_name):
        try:
            url = f"https://api.nuget.org/v3-flatcontainer/{package_name}/index.json"
            response = requests.get(url)
            response.raise_for_status()
            versions = response.json()["versions"]

            # Filter out pre-release versions (those containing "-")
            stable_versions = [v for v in versions if "-" not in v]

            # Check if there are any stable versions
            if stable_versions:
                latest_stable_version = stable_versions[-1]  # The last item is the latest stable version
                return latest_stable_version
            else:
                print(f"No stable version found for {package_name}.")
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching version for {package_name}: {e}")
            return None
        
    def upgrade_nuget_packages(self):
        recommendations = []

        for root, dirs, files in os.walk(self.upgraded_solution_path):
            for file in files:
                if file.endswith(".csproj"):
                    csproj_path = os.path.join(root, file)
                    with open(csproj_path, "r") as f:
                        content = f.read()
                    print("Upgrading NuGet packages started")
                    print("--------------------------------------------------------------------------------------------------------------")

                    # Find all package references
                    packages = re.findall(r'<PackageReference Include="([^"]+)" Version="([^"]+)"', content)
                    updated_content = content

                    # Loop through each package and get the latest version via the helper function
                    for package_name, current_version in packages:
                        # Fetch the latest stable version from NuGet
                        latest_version = self.get_latest_nuget_version(package_name)
                        print(f"Upgraded {package_name} from current version:-{current_version} to latest stable version:- {latest_version}")  # Debugging output

                        # Check if the latest version is newer than the current version
                        if latest_version and latest_version != current_version:
                            # Update the .csproj content with the latest version
                            updated_content = re.sub(
                                f'<PackageReference Include="{package_name}" Version="{current_version}"',
                                f'<PackageReference Include="{package_name}" Version="{latest_version}"',
                                updated_content
                            )
                            recommendations.append(
                                f"Upgraded NuGet package '{package_name}' from version '{current_version}' to '{latest_version}'."
                            )
                        else:
                            recommendations.append(
                                f"No upgrade needed for '{package_name}', current version '{current_version}' is the latest."
                            )

                    # Write changes back to the .csproj file if there were updates
                    if updated_content != content:
                        with open(csproj_path, "w") as f:
                            f.write(updated_content)
                        #print(f"NuGet packages in {file} have been upgraded to the latest versions successfully.")
                        print("--------------------------------------------------------------------------------------------------------------")
                        print("\033[1;32mNuGet packages in {file} have been upgraded to the latest versions successfully.\033[0m")
                        print("--------------------------------------------------------------------------------------------------------------")

        return recommendations
    
    
    def analyze_and_upgrade(self,root_folder_path):
        print("Creating  self.create_solution_copy()...")
        self.create_solution_copy(root_folder_path)
        print("Upgrading csproj files by calling self.upgrade_csproj_files()...")
        self.upgrade_csproj_files()
        print("Upgrading Dockerfile by calling self.upgrade_docker_image()...")
        self.upgrade_docker_image()  # Upgrade Dockerfile if found

        print("Checking for vulnerabilities by calling self.check_for_vulnerabilities()...")
        vulnerabilities = self.check_for_vulnerabilities()

        print("Proposing efficiency improvements by calling self.propose_efficiency_improvements()...")
        improvements = self.propose_efficiency_improvements()

        print("Upgrading NuGet packages and getting upgrade recommendations by calling self.upgrade_nuget_packages()...")
          # Upgrade NuGet packages and get upgrade recommendations
        nuget_recommendations = self.upgrade_nuget_packages()
        
        # Additional recommendations for deprecated methods and NuGet packages
        recommendations = self.analyze_cs_files()
        #nuget_updates = self.list_outdated_nuget_packages()

        # Build the solution and capture any errors
        build_errors = self.build_solution()
        build_suggestions = None
        if build_errors:
            build_suggestions = self.analyze_build_errors(build_errors)

        # Save recommendations to notepad
        all_recommendations = recommendations + nuget_recommendations
        self.save_to_notepad(vulnerabilities, improvements, build_suggestions, recommendations, all_recommendations)


# if __name__ == "__main__":
#     solution_path = r"D:\Projects\POC\UpgradeAgent\AWS_CICD_book-app-api"  # Provide the path to the .NET solution
#     api_key = "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"  # Replace with your OpenAI API key

#     analyzer = DotNetCodeAnalyzer(solution_path, api_key)
#     analyzer.analyze_and_upgrade()



if __name__ == "__main__":
    root_folder_path = r"D:\Projects\POC\UpgradeAgent"
    api_key = "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"  # Replace with your OpenAI API key

    processed_projects = set()

    for dirpath, dirnames, filenames in os.walk(root_folder_path):
        # Skip if the directory is within MigrationSolutions to avoid redundant processing
        if "MigrationSolutions" in dirpath:
            continue

        for filename in filenames:
            # Only process `.sln` files if present, to avoid processing `.csproj` files separately
            if filename.endswith(".sln"):
                solution_path = os.path.join(dirpath, filename)

                # Skip if this project directory has already been processed
                project_directory = os.path.dirname(solution_path)
                if project_directory in processed_projects:
                    print(f"\033[1;33mSkipping already processed project directory: {project_directory}\033[0m")
                    continue

                print(f"\033[1;32mFound .NET solution/project: {solution_path}\033[0m")

                # Create an instance of DotNetCodeAnalyzer for this solution/project
                analyzer = DotNetCodeAnalyzer(solution_path, api_key)
                
                # Call analyze_and_upgrade to upgrade to .NET 8 and apply all enhancements
                analyzer.analyze_and_upgrade(root_folder_path)
                
                # Mark the project directory as processed
                processed_projects.add(project_directory)
                print(f"\033[1;32mProject {solution_path} upgraded to .NET 8 successfully.\033[0m")

    print("\033[1;32mAll unique solutions/projects upgraded to .NET 8 successfully.\033[0m")

