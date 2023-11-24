# Introduction

This help file guides one through the steps of running the solution in windows using [Docker Desktop](https://www.docker.com/products/docker-desktop/) :tm. Step-by-step installation is not in-scope for this document.

## Prerequisites

1. [Docker Desktop](https://www.docker.com/products/docker-desktop/) :tm. If the link is not clickable for some reason, it is provided here: `https://www.docker.com/products/docker-desktop/` to copy and paste in a browser window.
1. Compatible MS Windows :tm version. No support can be provided for incompatible versions

# Steps

## Launch docker desktop with or without signup

This step will only be relevant once per Docker Desktop :tm installation.

!["Start Docker Desktop" dialogue](./media/01_start_docker_desktop.png)

## Download container image

This step will also not be necessary every time. Getting the latest image tag if available is recommended; however, trying a fresh `Pull` on the current image is safe and may lead to updating the latest version, in case there have been fixes for the latest version.

NOTE: At the time of writing this (24-11-2023) the valid tag is `0.1.0`. The tag shown, `0.1.1` has been removed for versioning reasons.

![Download container image](./media/02_get_image.png)

Using the search-bar in the top of the Docker Desktop :tm window search for the repository containing the image. The full string `constantinosstsolomonides/excel_converter` may be used, but will most likely not be required, as the result will be found once there are no other possible matches.

Once the image is retrieved, select the appropriate `Tag` and hit `Pull`. That will lead to the following notifications begining to pop-up and disappearing:

![Image pull progress notifications](./media/03_image_pull_ongoing.png)

## Mount host folder in container

To gain access to the files to be processed inside the container, the folder containing them must be linked. To start (run) a container with the folder mounted, start by clicking on the three vertical dots in the image row under `Images` menu (left pane)

![Special options menu](./media/04_add_special_options.png)

Click on `Host path` under `Volumes` and navigate to the folder that will be made available inside the container:


![Mount host volume](./media/05_mount_host_path.png)

Then, select the mount path inside the container where the folder will be made available. It is recommended to use `/opt/excel_converter/files/`, the same path used in the Linux example, and the one used in the example commands. Following the selection, hit `Run`

![Set in-container path](./media/06_select_in-container_location.png)

## In-container access

To access the command-line inside the container, go to `Containers` menu on the left pane, select the container and go to `Exec` tab. This provides access in the same way as in the original instructions. From there, the steps are as for under Linux in the ["Calling via Docker Image" section of the README](./README.md#calling-via-docker-image)
