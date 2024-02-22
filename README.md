# CDL-Project - Wildfire Detection

### So far:

+ API Calls to get Data from Sensors (humidity, temperature, smoke level)
+ Function to calculate distance to real wildfires and select best sensors
+ Integrate Weather Data
+ EDA, Data Cleaning & Analysis


### Next:
+ Get Granular Data (hourly)
+ Feature Engineering
+ Tableau Dashboard completed

# Infrastructure Setup · Cloud Side

This section walks users through setting up the controller for the edge network. Prerequisites include golang to support KubeEdge, as well as a container runtime (we will use containerd as dockershim/cri-docker are deprecated). Containerd ships with Docker ≥ 18.09 but we don't need the rest of Docker's functions, so we omit it.

## Install [golang 1.22.0](https://go.dev/doc/install)

```bash
# Download latest go gzip archive (edit URL as necessary)
wget https://go.dev/dl/go1.22.0.linux-amd64.tar.gz

# Delete existing go folder if it exists
sudo rm -rf /usr/local/go

# Untar the downloaded archive (might need to change filename)
sudo tar -C /usr/local -xzf go1.22.0.linux-amd64.tar.gz

# Add go folder to PATH
export PATH=$PATH:/usr/local/go/bin

# Reload source profile
source $HOME/.bash_profile
source $HOME/.bashrc
source $HOME/.profile

# Run version check to test function
go version
```

## Install [containerd 1.7.13](https://github.com/containerd/containerd/blob/main/docs/getting-started.md)

```bash
# Download latest .tar.gz
wget https://github.com/containerd/containerd/releases/download/v1.7.13/containerd-1.7.13-linux-amd64.tar.gz

# Unpack file to /usr/local
tar Cxzvf /usr/local containerd-1.7.13-linux-amd64.tar.gz

# Download the containerd.service unit file
wget https://raw.githubusercontent.com/containerd/containerd/main/containerd.service

# Move unit file to correct dir. Normally /usr/local/lib/systemd/system/ but on Ubuntu /lib/systemd/system/
sudo mv containerd.service /lib/systemd/system/

# Reload systemd daemons
sudo systemctl daemon-reload
sudo systemctl enable --now containerd

# Check service health
systemctl status containerd
```

### Configure containerd runc options
```bash
sudo mkdir /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml

# Edit config
nano /etc/containerd/config.toml

# Change SystemdCgroup = false to true
SystemdCgroup = true
```

### Install [runc](https://github.com/opencontainers/runc/releases)

```bash
# Download the latest runc.<ARCH> binary 
wget https://github.com/opencontainers/runc/releases/download/v1.1.12/runc.amd64

# Install to sbin
sudo install -m 755 runc.amd64 /usr/local/sbin/runc
```

### Install [CNI Plugins](https://github.com/containernetworking/plugins/releases)

```bash
# Download the cni-plugins-<OS>-<ARCH>-<VERSION>.tgz archive
wget https://github.com/containernetworking/plugins/releases/download/v1.4.0/cni-plugins-linux-amd64-v1.4.0.tgz

# Extract it under /opt/cni/bin
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.4.0.tgz
```

## Install [kubeadm + kubectl + kubelet v1.26](https://v1-26.docs.kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/)

```bash
# Update the apt package index and install packages
sudo apt update
sudo apt install -y apt-transport-https ca-certificates curl

# Download the public signing key for the Kubernetes package repositories.
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.26/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

# Add the appropriate Kubernetes apt repository. This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes.list
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.26/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

# Update the apt package index, install kubelet, kubeadm and kubectl, and pin their version:

sudo apt update
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### Enable bash completion for kubectl (optional)
```bash
kubectl completion bash | sudo tee /etc/bash_completion.d/kubectl > /dev/null

echo "source <(kubectl completion bash)" >> ~/.bashrc
echo "source <(kubectl completion bash)" >> ~/.bash_profile
echo "source <(kubectl completion bash)" >> ~/.profile
```

### Verify cgroup driver is systemd
```bash
kubeadm config print init-defaults
```

### Disable swap
```bash
sudo swapoff -a 
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```

### Forward IPv4 and config iptables for bridged traffic
```bash
cat <<EOF | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

# sysctl params required by setup, params persist across reboots
cat <<EOF | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOF

# Apply sysctl params without reboot
sudo sysctl --system
```

Verify that the `br_netfilter`, `overlay` modules are loaded by running the following commands:

```bash
lsmod | grep br_netfilter
lsmod | grep overlay
```

Verify that the `net.bridge.bridge-nf-call-iptables`, `net.bridge.bridge-nf-call-ip6tables`, and `net.ipv4.ip_forward` system variables are set to `1` in your sysctl config by running the following command:

```bash
sysctl net.bridge.bridge-nf-call-iptables net.bridge.bridge-nf-call-ip6tables net.ipv4.ip_forward
```
### Initialize kubeadm control plane
```bash
sudo kubeadm init --apiserver-advertise-address 129.105.89.200 --pod-network-cidr=10.244.0.0/16
```

### Copy configs to .kube directory
```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

### Install [Flannel CNI](https://github.com/flannel-io/flannel)
```bash
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

### Set up KubeEdge
```bash
wget https://github.com/kubeedge/kubeedge/releases/download/v1.15.2/keadm-v1.15.2-linux-amd64.tar.gz
tar -zxvf keadm-v1.15.2-linux-amd64.tar.gz
cp keadm-v1.15.2-linux-amd64/keadm/keadm /usr/local/bin/keadm

# Add keadm to $PATH
echo 'export PATH=$PATH:/usr/local/bin/keadm/' >> $HOME/.bash_profile

# Untaint control plane node to allow KubeEdge to schedule onto it
kubectl taint nodes cdl-k8s-control node-role.kubernetes.io/control-plane:NoSchedule-
```

### Initialize services with keadm
```bash
keadm init --advertise-address=129.105.EXTERNAL.IP --profile version=v1.12.1 --kube-config=/root/.kube/config
```

### Verify KubeEdge nodes running
```bash
kubectl get all -n kubeedge
```

## Useful `kubectl` commands to check cluster health
```bash
kubectl cluster-info
```
This should give the IP address of the control plane; we also want to see CoreDNS info present.

```bash
kubectl get nodes
```
This will list all nodes in the cluster.

```bash
kubectl describe node
```
Lists more in depth information for each node in the cluster.

```bash
kubeadm reset --cleanup-tmp-dir 
rm -rf /etc/kubernetes/ /etc/cni/net.d $HOME/.kube
```
Reset the cluster in preparation for reinit

# Infrastructure Setup · Edge Side

First step for setting up the raspberry pi's is to load a ubuntu server image on it using this [tutorial](https://ubuntu.com/tutorials/how-to-install-ubuntu-on-your-raspberry-pi#1-overview).

The rest of this section walks users through setting up raspberry pi's as edge nodes for the edge network. The first step is setting up the pi for network connectivity. Then, prerequisites to support KubeEdge include golang, a container runtime (we will use containerd as dockershim/cri-docker are deprecated), and mosquitto.

## WIFI Connectivity

To allow connectivty, the pi's MAC address needs to be added to the Devices Northwestern portal and the netplan on the pi needs to be edited.

### Add MAC Address to portal

To add a MAC address to the Northwestern portal, use this [portal link](device.wireless.northwestern.edu). If you don't have the MAC address for the pi recorded, when you connect the pi to a monitor and keyboard and then boot it run the following command:

```bash
ip link
```

Look for the address under wlan0 and link/ether.

### Edit Netplan

To edit the netplan file, find it using this command:

```bash
sudo vim /etc/netplan/50-cloud-init.yaml
```

Then edit the file to reflect his format

```bash
network:
    version: 2
    wifis:
        renderer: networkd
        wlan0:
            dhcp4: true
            access-points:
                "Device-Northwestern": {}
```

Run the next command to restart the network daemon and connect to WiFi.

```bash
sudo netplan apply
```

Wait for the connection, then check the ip address.

```bash
ip a
```

You can then use that ip address for the wlan0 connection to ssh into the device.

```bash
ssh admin@{ip_address}
```

## Dependency Installation

### Install [golang 1.22.0](https://go.dev/doc/install)

```bash
# Download latest go gzip archive (edit URL as necessary)
wget  https://go.dev/dl/go1.21.7.linux-arm64.tar.gz

# Delete existing go folder if it exists
sudo rm -rf /usr/local/go

# Untar the downloaded archive (might need to change filename)
sudo tar -C /usr/local -xzf go1.21.7.linux-arm64.tar.gz

# Add go folder to PATH
export PATH=$PATH:/usr/local/go/bin

# Reload source profile
source $HOME/.bashrc
source $HOME/.profile

# Run version check to test function
go version
```

### Install [containerd 1.7.13](https://github.com/containerd/containerd/blob/main/docs/getting-started.md)

```bash
# Download latest .tar.gz
wget https://github.com/containerd/containerd/releases/download/v1.7.13/containerd-1.7.13-linux-arm64.tar.gz

# Unpack file to /usr/local
sudo tar Cxzvf /usr/local containerd-1.7.13-linux-arm64.tar.gz

# Download the containerd.service unit file
wget https://raw.githubusercontent.com/containerd/containerd/main/containerd.service

# Move unit file to correct dir. Normally /usr/local/lib/systemd/system/ but on Ubuntu /lib/systemd/system/
# You may need to create the below directory before moving the file over
sudo mv containerd.service /lib/systemd/system/

# Reload systemd daemons
sudo systemctl daemon-reload
sudo systemctl enable --now containerd

# Check service health
systemctl status containerd
```

### Install [mosquitto](https://mosquitto.org/download/)

```bash
sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa
sudo apt-get update
```
