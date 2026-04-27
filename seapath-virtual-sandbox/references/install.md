# SEAPATH Virtual Sandbox — one-time bootstrap

Read this file **only** when the sandbox repo (or the SEAPATH ansible repo) is missing locally. Once both repos exist and the host prereqs are in place, return to `SKILL.md` — none of the steps below need to be repeated.

## 1. Pick a parent directory

The two repos must be siblings so that the Makefile's default `ANSIBLE_REPO=./ansible` (or the common override `../ansible`) resolves correctly. Pick a working directory and `cd` into it before cloning. Ask the user if no obvious choice exists.

## 2. Clone both repos

```bash
git clone https://github.com/dupremathieu/seapath-virtual-sandbox.git
git clone https://github.com/seapath/ansible.git
```

Resulting layout:

```
<parent>/
├── seapath-virtual-sandbox/   # this skill operates here
└── ansible/                   # SEAPATH Ansible repo (used by make ansible-setup)
```

With this layout, every `ansible-*` Make target needs `ANSIBLE_REPO=../ansible`. Alternatively, clone (or symlink) the ansible repo as `seapath-virtual-sandbox/ansible` to use the Makefile default.

## 3. Install the SEAPATH Ansible dependencies

The SEAPATH ansible repo ships a `prepare.sh` that installs `ansible-core` 2.16, the required collections, and Python deps:

```bash
cd ansible
./prepare.sh
cd ..
```

If the user prefers a containerised workflow, the sandbox repo also exposes [cqfd](https://github.com/savoirfairelinux/cqfd) flavors (`cqfd init`, `cqfd -b ansible`, `cqfd -b terraform`, etc.). Only `libvirtd` and Docker/Podman are then needed on the host. See the sandbox `README.md` "Containerised workflow with cqfd" section.

## 4. Verify host prerequisites

Run on the host (not inside a container):

```bash
systemctl status libvirtd openvswitch
which terraform virsh ovs-vsctl
```

Required:

- `libvirt` / `qemu-kvm` running (`libvirtd` active).
- `openvswitch` running. The cluster ring uses RSTP BPDUs that Linux bridges silently drop, so OVS host-side bridges are mandatory.
- `terraform` ≥ 1.3 with the `dmacvicar/libvirt` provider (fetched on `make init`).
- `virsh` CLI (`libvirt-client`).
- `ansible` 2.16 — installed by `prepare.sh` above.

Install whichever is missing using the host's package manager.

### Passwordless sudo for `ovs-vsctl`

`make apply` and `make destroy` call `sudo ovs-vsctl add-br/del-br` to manage host-side ring bridges. Add a sudoers drop-in so these calls don't prompt:

```bash
echo "$(whoami) ALL=(root) NOPASSWD: /usr/bin/ovs-vsctl" \
  | sudo tee /etc/sudoers.d/seapath-sandbox-ovs
sudo chmod 440 /etc/sudoers.d/seapath-sandbox-ovs
```

## 5. Provide a SEAPATH qcow2 image

Terraform clones the VMs from a base qcow2. The image must:

- Boot Debian or Yocto with cloud-init disabled (or already configured).
- Contain an `ansible` user.
- Have the host user's SSH **public** key in `/home/ansible/.ssh/authorized_keys` (the inventory connects as `ansible@<node-ip>`).

This is a property of the image build and cannot be patched from the sandbox. Either reuse an existing SEAPATH image or build one with the user's key baked in.

## 6. Create `terraform/terraform.tfvars`

```bash
cd seapath-virtual-sandbox
cp terraform.tfvars.example terraform/terraform.tfvars
$EDITOR terraform/terraform.tfvars   # set base_image_path at minimum
```

`terraform/terraform.tfvars` is gitignored. The only required value is `base_image_path` pointing at the qcow2 from step 5. All other variables (RAM, vCPUs, disk size, libvirt URI) have sensible defaults in `terraform/variables.tf`.

## 7. Done — return to SKILL.md

Once the layout looks like:

```
<parent>/
├── seapath-virtual-sandbox/
│   └── terraform/terraform.tfvars   # exists, base_image_path set
└── ansible/                         # prepare.sh has been run
```

…and `systemctl status libvirtd openvswitch` reports both active, return to `SKILL.md` and proceed to the "Bring the cluster up" section. Subsequent runs do not need this file.
