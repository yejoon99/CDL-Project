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

Then manually add the following lines to the file: /run/flannel/subnet.env
```bash
FLANNEL_NETWORK=10.244.0.0/16
FLANNEL_SUBNET=10.244.0.1/24
FLANNEL_MTU=1450
FLANNEL_IPMASQ=true
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

### Install [mosquitto](https://mosquitto.org/documentation/using-the-snap/)

```bash
snap install mosquitto
```

### Install [CNI Plugins](https://github.com/containernetworking/plugins/releases)

```bash
# Download the cni-plugins-<OS>-<ARCH>-<VERSION>.tgz archive
wget https://github.com/containernetworking/plugins/releases/download/v1.4.0/cni-plugins-linux-amd64-v1.4.0.tgz

# Extract it under /opt/cni/bin
sudo mkdir -p /opt/cni/bin
sudo tar Cxzvf /opt/cni/bin cni-plugins-linux-amd64-v1.4.0.tgz
```

### Install [runc](https://github.com/opencontainers/runc/releases)

```bash
# Download the latest runc.<ARCH> binary 
wget https://github.com/opencontainers/runc/releases/download/v1.1.12/runc.arm64

# Install to sbin
sudo install -m 755 runc.arm64 /usr/local/sbin/runc
```

### Edit Flannel Config
```bash
sudo touch /run/flannel/subnet.env
sudo vim /run/flannel/subnet.env
```
Add the following lines to the file above.
```bash
FLANNEL_NETWORK=10.244.0.0/16
FLANNEL_SUBNET=10.244.0.1/24
FLANNEL_MTU=1450
FLANNEL_IPMASQ=true
```

### Set up KubeEdge
```bash
sudo wget https://github.com/kubeedge/kubeedge/releases/download/v1.15.2/keadm-v1.15.2-linux-arm64.tar.gz
sudo tar -zxvf keadm-v1.15.2-linux-arm64.tar.gz
sudo cp keadm-v1.15.2-linux-arm64/keadm/keadm /usr/local/bin/keadm

# Add keadm to $PATH
echo 'export PATH=$PATH:/usr/local/bin/keadm/' >> $HOME/.bash_profile

# Check that this final command runs
keadm join --help
```

### Kill kube-proxy if it's running
Check whether or not kube-proxy is running and kill it if it is.
```bash
#Install net-tools
sudo apt install net-tools

#Identify kube-proxy PID
netstat -tulp | grep kube-proxy
```

```bash
#kill the process
kill -9 <kube-propxy-PID>
```

### Connect to KubeEdge cloudcore
```bash
sudo keadm join --cloudcore-ipport=129.105.89.200:10000 --edgenode-name=<edge node name> --token=9264837828f5d6987b52a8678d4318756bd1ca482528000b5769d2c261a6a0f8.eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3MTI5NDY1ODB9.a0QH9Q_VdSn-q50KE8a5EFUNOCuCv7xES5mYytDuLkU
```
# Deploy ML

## Run Docker

### First Test: run Docker on local Machine
```bash
docker build -t image_rpi .
docker run image_rpi
```
Docker Image is uploaded on Docker Hub under the name ""

### Second Test: run python script on Raspberry Pi
copy from local folder onto R-Pi:
```bash
scp -r docker-files admin@10.106.11.115:/home/admin
```
on R-Pi:
Then on r-pi:

```bash
# Cd in docker-files
# Create virtual environment:
python3 -m venv venv_name
source venv_test/bin/activate

pip install -r requirements.txt
python3 script.py
```

### Push to docker hub:
```bash
docker tag <image_id> <username>/<repository_name>:<tag>
docker login
docker push <username>/<repository_name>:<tag>
```

Our Image:
Repository name: cdl_kubeedge_wildfire
Tag: V1

### Third Test: run python script in Container on Raspberry Pi

(sudo apt install docker.io) - Did not work?
docker pull <username>/<repository_name>:<tag>
docker run <username>/<repository_name>:<tag>


## Stream Data via Fast API

# Model Execution Pipeline

## Setup
First, ensure you have all necessary libraries installed and imported in your script or Jupyter notebook:

```bash
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.utils import resample
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score, accuracy_score
from imblearn.over_sampling import RandomOverSampler
from sklearn.preprocessing import StandardScaler
```

# Data Preprocessing

## 1. Data Cleaning and Preparation
Begin by running the preprocess_data function to clean your dataset. This function performs several key operations:

1. Converts the 'date' column to datetime format and extracts the month.
2. Creates dummy variables for each month.
3. Removes unnecessary columns.
4. Scales numerical features except for the target variable.

```bash
import pandas as pd

data = pd.read_csv('path/to/your/dataset.csv')
processed_data = preprocess_data(data)
```

## 2. Separate Blind Test Set
If your data contains a 'year' column that has been scaled, you can separate out a blind test set for final evaluation.
```bash
blind_test_set = separate_blind_dataset(processed_data)
```
## 3. Balance the Dataset
To balance your dataset, you have two options: downsampling the majority class or oversampling the minority class. Choose the method that best fits your scenario.

### Downsampling Majority Class
This method reduces the majority class to match the size of the minority class. Use the downsample_majority_class function provided.
```bash
balanced_data = downsample_majority_class(processed_data)
```
### Oversampling Minority Class
This method increases the minority class to match the size of the majority class. Use the random_over_sampling function for this purpose. Note that you should perform this step after splitting your data into training and testing sets to avoid overfitting.
```bash
from sklearn.model_selection import train_test_split

X = balanced_data.drop('target', axis=1)
y = balanced_data['target']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=123)

X_train_resampled, y_train_resampled = random_over_sampling(X_train, y_train)
```

# Model Training with Cross-Validation by Sensor ID
This section explains how to train the Logistic Regression, Random Forest Classifier, and MLP Classifier models with cross-validation, grouped by sensor_id. The training process includes hyperparameter tuning using GridSearchCV and evaluation on both test and blind datasets.

## Defining Parameter Grids
First, define the parameter grids for each model. Adjust the parameter ranges based on your dataset's specifics and the models' requirements.
```bash
param_grids = {
    'Logistic Regression': {
        'param_grid': {'C': [0.1, 1, 10], 'penalty': ['l2']},
        'train_fn': train_logistic_regression
    },
    'Random Forest': {
        'param_grid': {'n_estimators': [10, 100, 200], 'max_depth': [None, 10, 20, 30]},
        'train_fn': train_random_forest
    },
    'Neural Network': {
        'param_grid': {'hidden_layer_sizes': [(50,), (100,)], 'alpha': [0.0001, 0.001, 0.01]},
        'train_fn': train_neural_network
    }
}
```

## Training and Evaluation Pipeline
Utilize the provided pipeline functions to preprocess your data, balance it, perform cross-validated training, and evaluate the models. Choose the appropriate pipeline based on your dataset balancing strategy (e.g., undersampling or SMOTE)

### Undersampling Pipeline
```bash
# Assuming `data` is your DataFrame containing the dataset
X_train, X_test, y_test, blind_set, best_models, cv_scores = run_pipeline_undersampling(data, param_grids)

# Print Cross-Validation scores
for model_name, scores in cv_scores.items():
    print(f"{model_name} CV Scores:", scores)
```

### Oversampling Pipeline
```bash
X_train, X_test, y_test, blind_set, best_models, cv_scores = run_pipeline_smote(data, param_grids)

# Print Cross-Validation scores
for model_name, scores in cv_scores.items():
    print(f"{model_name} CV Scores:", scores)
```

# Evaluating Models on the Test Set
After training your models using either the undersampling or oversampling pipelines, it's crucial to assess their performance on a separate test set. This process helps to understand how well the models might perform on unseen data. The evaluation covers several key metrics, including the confusion matrix, precision, recall, F1 score, and accuracy.

### Undersampling
```bash
# Evaluate models on the test set
test_evaluation_results = {}
for clf_name, model in best_models.items():
    test_evaluation_results[clf_name] = evaluate_model(model, X_test, y_test)

# Display evaluation metrics for the test set
for clf_name, evaluation_metrics in test_evaluation_results.items():
    print(f"Performance of {clf_name} on the Test Set:")
    print("Confusion Matrix:\n", evaluation_metrics['confusion_matrix'])
    print("Precision: {:.2f}".format(evaluation_metrics['precision']))
    print("Recall: {:.2f}".format(evaluation_metrics['recall']))
    print("F1 Score: {:.2f}".format(evaluation_metrics['f1_score']))
    print("Accuracy: {:.2f}".format(evaluation_metrics['accuracy']))
    print()
```
### Oversampling 
```bash
# Evaluate models on the test set
test_evaluation_results = {}
for clf_name, model in models_oversampling.items():
    test_evaluation_results[clf_name] = evaluate_model(model, X_test, y_test)

# Display evaluation metrics for the test set
for clf_name, evaluation_metrics in test_evaluation_results.items():
    print(f"Performance of {clf_name} on the Test Set:")
    print("Confusion Matrix:\n", evaluation_metrics['confusion_matrix'])
    print("Precision: {:.2f}".format(evaluation_metrics['precision']))
    print("Recall: {:.2f}".format(evaluation_metrics['recall']))
    print("F1 Score: {:.2f}".format(evaluation_metrics['f1_score']))
    print("Accuracy: {:.2f}".format(evaluation_metrics['accuracy']))
    print()
```

# Feature Importance Evaluation for Models
Evaluating feature importance is an integral part of understanding the influence of each feature on the model predictions. In the case of Random Forest, this is particularly insightful as it assigns a score to each feature, indicating its importance in the decision-making process of the model.

## Extracting Feature Importance from Random Forest
The trained Random Forest model allows us to extract the importance of each feature. Here's how you can obtain and sort the feature importances.

### Undersampling
```bash
models_undersampling  = best_models

rf_model = models_undersampling['Random Forest']

# Get feature names
feature_names = X_train.columns

# Get feature importances
feature_importances = rf_model.feature_importances_

# Combine feature names and importances
features_and_importances = zip(feature_names, feature_importances)

# Sorting the features by importance
sorted_features_and_importances = sorted(features_and_importances, key=lambda x: x[1], reverse=True)

# Printing the sorted features and their importances
for feature, importance in sorted_features_and_importances:
    print(f"{feature}: {importance}")
```

### Oversampling
```bash
models_oversampling = best_models
rf_model = models_oversampling['Random Forest']

feature_names = X_train.columns

feature_importances = rf_model.feature_importances_

features_and_importances = zip(feature_names, feature_importances)

# Sorting the features by importance
sorted_features_and_importances = sorted(features_and_importances, key=lambda x: x[1], reverse=True)

# Printing the sorted features and their importances
for feature, importance in sorted_features_and_importances:
    print(f"{feature}: {importance}")
```

# Evaluating Models on the Blind Test Set
Once your models have been trained and validated, the next critical step is to evaluate their performance on a blind test set. This dataset should not have been used during the training or validation phases, ensuring that the evaluation metrics reflect the model's ability to generalize to new, unseen data.

### Undersampling
```bash
# Evaluate undersampling models on the blind test set
blind_evaluation_results = {}
for clf_name, model in models_undersampling.items():
    blind_evaluation_results[clf_name] = evaluate_on_blind_set(model, blind_set)

# Display evaluation metrics for the blind test set
for clf_name, evaluation_metrics in blind_evaluation_results.items():
    print(f"Performance of {clf_name} on the Blind Test Set:")
    print("Confusion Matrix:\n", evaluation_metrics['confusion_matrix'])
    print(f"Precision: {evaluation_metrics['precision']:.2f}")
    print(f"Recall: {evaluation_metrics['recall']:.2f}")
    print(f"F1 Score: {evaluation_metrics['f1_score']:.2f}")
    print(f"Accuracy: {evaluation_metrics['accuracy']:.2f}")
    print()
```

### Oversampling
```bash
# Evaluate undersampling models on the blind test set
blind_evaluation_results = {}
for clf_name, model in models_oversampling.items():
    blind_evaluation_results[clf_name] = evaluate_on_blind_set(model, blind_set)

# Display evaluation metrics for the blind test set
for clf_name, evaluation_metrics in blind_evaluation_results.items():
    print(f"Performance of {clf_name} on the Blind Test Set:")
    print("Confusion Matrix:\n", evaluation_metrics['confusion_matrix'])
    print(f"Precision: {evaluation_metrics['precision']:.2f}")
    print(f"Recall: {evaluation_metrics['recall']:.2f}")
    print(f"F1 Score: {evaluation_metrics['f1_score']:.2f}")
    print(f"Accuracy: {evaluation_metrics['accuracy']:.2f}")
    print()
```

# Interpreting the Results
The evaluation metrics provide insights into each model's performance:

1. Confusion Matrix: Shows the number of correct and incorrect predictions, broken down by each class.
   
2. Precision: The ratio of correctly predicted positive observations to the total predicted positives. High precision relates to a low false positive rate.
   
3. Recall (Sensitivity): The ratio of correctly predicted positive observations to the all observations in the actual class. High recall indicates most of the positive class is correctly recognized.
   
4. F1 Score: The weighted average of Precision and Recall. Therefore, this score takes both false positives and false negatives into account. Useful for uneven class distribution.
   
5. Accuracy: The ratio of correctly predicted observation to the total observations. Can be misleading if classes are imbalanced.
Using these metrics, you can gauge the strengths and weaknesses of each model relative to your specific needs and dataset characteristics.
