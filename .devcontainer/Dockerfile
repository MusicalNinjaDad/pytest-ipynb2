FROM docker.io/library/fedora:41

# ---
# Setup base system ...
# ---

# Enable man pages by commenting out the nodocs flag
COPY <<EOF /etc/dnf/dnf.conf
[main]
gpgcheck=True
installonly_limit=3
clean_requirements_on_remove=True
best=False
skip_if_unavailable=True
# tsflags=nodocs
EOF

# Create the default user - most agents mount workspace directory chowned to 1000:1000
ARG USERNAME=pyo3
ARG USER_UID=1000
ARG USER_GID=${USER_UID}
RUN groupadd --gid ${USER_GID} ${USERNAME} \
    && useradd --uid ${USER_UID} --gid ${USER_GID} -m ${USERNAME} \
    && echo ${USERNAME} ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/${USERNAME} \
    && chmod 0440 /etc/sudoers.d/${USERNAME}

# ---
# Install ...
# ---

# Man pages for all the stuff which is already installed, man itself and basic manpages
RUN dnf -y --setopt=install_weak_deps=False install \
    man \
    man-db \
    man-pages \
    && dnf -y update \
    && dnf -y --setopt=install_weak_deps=False reinstall --skip-unavailable $(dnf list --installed | awk '{print $1}')

# Basic development tools
RUN dnf -y --setopt=install_weak_deps=False install \
    bash-completion \
    git \
    just \
    which

# Python
RUN dnf -y install \
    python \
    python-pip

# python3.12, g++ and python-headers for pytype
RUN dnf -y --setopt=install_weak_deps=False install \
    gcc-c++ \
    python3.12 \
    python3.12-devel

#uv for fast python package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# nbstripout - git siff & strip handling for jupyter metadata. (Needs to be activated in workspace)
RUN uv pip install --system nbstripout

# ---
# Final setup steps
# ---


# Set the default user
USER ${USERNAME}
