#! /usr/bin/bash

cd $(dirname $0)
gpg --import primary-public-key.txt

# Verify the signer fingerprint
fingerprint=$(gpg --import signer-public-key.txt | sed -n '/gpg: key /s/.*key \([A-F0-9]*\).*/\1/p')
gpg --fingerprint $fingerprint | grep -q "37D8 BE16 0355 2DA7 BD6A  04D8 C7A0 5F43 FE0A DDFA"
if [ $? -ne 0 ]; then
    echo "Error: Fingerprint verification failed."
    exit 1
fi
gpg --check-sigs $fingerprint | grep -q "1 signature not checked due to a missing key"
if [ $? -eq 0 ]; then
    echo "Error: Public key verification failed."
    exit 1
fi
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-arm64.zip
wget https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-arm64.zip.sig
gpg --verify aws-sam-cli-linux-arm64.zip.sig aws-sam-cli-linux-arm64.zip
if [ $? -ne 0 ]; then
    echo "Error: Signature verification failed."
    exit 1
fi

unzip -q aws-sam-cli-linux-arm64.zip -d aws-sam-cli-linux-arm64
if [ ! -d $HOME/.local ]; then
    mkdir $HOME/.local
fi
./aws-sam-cli-linux-arm64/install -i $HOME/.local/aws-sam-cli -b $HOME/.local/bin
