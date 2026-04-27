---
name: seapath-virtual-sandbox
description: Provision, boot, and operate the 3-node SEAPATH virtual sandbox (QEMU/KVM via Terraform + Ansible). Use when the user wants to start/stop the cluster, run the SEAPATH Ansible setup, connect to nodes, or run tests against the sandbox. Designed to be used by any AI coding agent (Claude Code, OpenCode, etc.) and works whether or not the sandbox repo is the current working directory.
---

# SEAPATH Virtual Sandbox

The [seapath-virtual-sandbox](https://github.com/dupremathieu/seapath-virtual-sandbox) repo provisions a 3-node SEAPATH cluster on QEMU/KVM. Terraform (dmacvicar/libvirt) creates the VMs and networks; the external [seapath/ansible](https://github.com/seapath/ansible.git) repo configures the cluster. All operations are wrapped by the `Makefile` at the sandbox repo root — prefer `make` targets over invoking `terraform` / `ansible-playbook` directly.

## Step 0 — Locate the sandbox repo (do this first)

Every command in this skill assumes the working directory is the sandbox repo root. Before doing anything else, locate it. The repo is recognised by having both a `Makefile` and a `terraform/` directory, plus `inventory/seapath-sandbox.yaml`.

Search in this order and `cd` into the first match:

```bash
for d in . ./seapath-virtual-sandbox ../seapath-virtual-sandbox ../../seapath-virtual-sandbox; do
  if [ -f "$d/Makefile" ] && [ -d "$d/terraform" ] && [ -f "$d/inventory/seapath-sandbox.yaml" ]; then
    SANDBOX_DIR="$(cd "$d" && pwd)"; echo "Found sandbox repo at: $SANDBOX_DIR"; break
  fi
done
```

- **If `SANDBOX_DIR` is set**: `cd "$SANDBOX_DIR"` and continue with the rest of this skill.
- **If no match was found**: the user does not yet have the sandbox cloned locally. Read `references/install.md` for the one-time bootstrap procedure (clone the sandbox repo, clone the SEAPATH ansible repo, install host dependencies, create `terraform/terraform.tfvars`). Do not load `install.md` otherwise — it is irrelevant once the repo is present.

The same applies to the SEAPATH ansible repo: by default the Makefile expects it at `./ansible` (relative to the sandbox repo). If it is at a different path, pass `ANSIBLE_REPO=<path>` on every `ansible-*` target (commonly `ANSIBLE_REPO=../ansible`). If `<sandbox>/ansible` does not exist and `<sandbox>/../ansible` does not exist either, also read `references/install.md`.

## Repo layout (what matters)

- `Makefile` — entry point for every operation
- `terraform/` — VM and network definitions; `terraform/terraform.tfvars` is gitignored and must be created from `terraform.tfvars.example`
- `inventory/seapath-sandbox.yaml` — Ansible inventory used by every `ansible-*` target
- `inventory/group_vars/all.yml` — sets `StrictHostKeyChecking=no` (host keys change on `terraform destroy`)
- The SEAPATH Ansible repo is **not** in this repo. It is expected at `./ansible` (default) or `../ansible`. Override with `ANSIBLE_REPO=<path>`.

## Bring the cluster up

Run from the sandbox repo root:

```bash
make init                                          # one-time: terraform init
make apply                                         # creates 3 VMs + 4 libvirt networks + 3 OVS bridges
make ansible-ping                                  # SSH reachability check (must pass before setup)
make ansible-setup ANSIBLE_REPO=<path-to-ansible>  # full pipeline
```

`make ansible-setup` runs `seapath_setup_main.yaml`. Individual phases run in this order if invoked manually:

```bash
make ansible-setup-network ANSIBLE_REPO=<...>   # OVS team0 + RSTP ring
make ansible-setup-ceph    ANSIBLE_REPO=<...>   # cephadm (cluster_setup_cephadm.yaml)
make ansible-setup-ha      ANSIBLE_REPO=<...>   # Pacemaker/Corosync
```

Pass extra ansible flags via `ANSIBLE_OPTS`, e.g. `ANSIBLE_OPTS="-v"` or `ANSIBLE_OPTS="--check"`.

Prerequisite: `terraform/terraform.tfvars` must exist and set `base_image_path` to a SEAPATH qcow2 image whose `ansible` user already has the host user's SSH key in `authorized_keys`. If the file is missing, see `references/install.md`.

## Lifecycle

| Goal                          | Command                                           |
|-------------------------------|---------------------------------------------------|
| Start all VMs                 | `make start`                                      |
| Graceful stop                 | `make stop` (falls back to force after timeout)   |
| Tear down everything          | `make destroy`                                    |
| Snapshot all VMs              | `make snapshot SNAPSHOT=<name>` (default `default`) |
| Restore all VMs               | `make restore SNAPSHOT=<name>`                    |
| List / delete snapshots       | `make snapshot-list` / `make snapshot-delete`     |

Take a snapshot named e.g. `post-setup` right after `ansible-setup` succeeds — restoring it is the fastest way to get back to a clean configured cluster between test runs.

`LIBVIRT_URI` defaults to `qemu:///system`. Override only if the user is running session-mode libvirt.

## Connecting to the nodes for tests

Four ways to reach the nodes — pick the one that matches the workflow:

1. **`make ssh-node{1,2,3}`** — interactive shell as `admin` with `sudo -s`. Strict host key checking is already disabled, so this works even after `make destroy && make apply`. Use for ad-hoc inspection.

2. **Direct `ssh`** — for scripted test commands, use the `ansible` user (the user the inventory connects as):
   ```bash
   ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
       ansible@192.168.100.101 -- <command>
   ```
   Node IPs: node1=`192.168.100.101`, node2=`192.168.100.102`, node3=`192.168.100.103`.

3. **`ansible` ad-hoc commands** — best for fan-out tests across the whole cluster. Always reference the sandbox inventory:
   ```bash
   ansible all          -i inventory/seapath-sandbox.yaml -m ping
   ansible hypervisors  -i inventory/seapath-sandbox.yaml -m shell -a "ovs-vsctl show"
   ansible mons         -i inventory/seapath-sandbox.yaml -m shell -a "ceph -s" -b
   ```
   Add `-b` for root. Use group names from the inventory (`hypervisors`, `cluster_machines`, `mons`, `osds`, `clients`).

4. **`make console-node{1,2,3}`** — virsh serial console. Use only when SSH/networking is broken (e.g. debugging `seapath-setup-network` failures). Exit with `Ctrl-]`.

## Ansible inventory: key facts

File: `inventory/seapath-sandbox.yaml`. Important when writing tests or new playbooks:

- **Connection user**: `ansible_user: ansible` (not `admin` — `admin` is only used by `make ssh-node*`).
- **Admin interface**: `network_interface: enp1s0` on every node.
- **Cluster ring interfaces** (used by OVS RSTP): `team0_0=enp2s0`, `team0_1=enp3s0`. Only meaningful inside `cluster_machines`.
- **Cluster IPs** (assigned statically by the network playbook, not by libvirt): node1=`192.168.55.1`, node2=`192.168.55.2`, node3=`192.168.55.3`. Subnet `192.168.55.0/24` is `cluster_network` / `public_network` for Ceph.
- **Ceph OSD disk**: `/dev/vdb` on every node (the second virtio disk created by Terraform).
- **No PTP, no isolcpus, no observers** — these are intentionally empty/omitted in the sandbox.

When a playbook needs only a subset of nodes, use the existing groups (`hypervisors`, `cluster_machines`, `mons`, `osds`, `clients`) rather than adding new ones.

## Verifying a healthy cluster

After `make ansible-setup`:

```bash
make ansible-ping

# OVS ring is up and RSTP converged (one port should be in BLOCKING state)
ansible cluster_machines -i inventory/seapath-sandbox.yaml -b \
    -m shell -a "ovs-vsctl show && ovs-appctl rstp/show team0"

# Ceph health
ansible node1 -i inventory/seapath-sandbox.yaml -b -m shell -a "ceph -s"

# Pacemaker
ansible node1 -i inventory/seapath-sandbox.yaml -b -m shell -a "crm_mon -1"
```

`ceph -s` should report `HEALTH_OK` with 3 mons and 3 OSDs (`up+in`). If Ceph mons fail to elect, the most common cause is a broken cluster ring — check OVS bridges on the host (`sudo ovs-vsctl list-br | grep ovs-ring`) and inside the guests.

## Common pitfalls

- **`make apply` fails on `ovs-vsctl`**: passwordless sudo for `ovs-vsctl` is missing. See `references/install.md`.
- **`ansible-ping` fails**: VM didn't boot, or the qcow2 image lacks the user's SSH key. Use `make console-node1` to confirm boot, then check `~ansible/.ssh/authorized_keys` inside the guest.
- **Host keys changed after recreate**: expected. The inventory disables strict host key checking; `make ssh-node*` does the same. Don't `ssh-keygen -R` — it's not needed.
- **`ANSIBLE_REPO` not set / wrong**: Makefile defaults to `./ansible`. If the SEAPATH ansible repo is elsewhere (commonly `../ansible`), pass `ANSIBLE_REPO=<path>` on every `ansible-*` target, or export it in the shell.
- **Out of RAM**: each node uses 4 GiB + 4 vCPUs. Full cluster needs ≥12 GiB free.

## When NOT to use this skill

This skill covers operating the sandbox. It does **not** cover modifying SEAPATH Ansible roles or playbooks — those live in the external `seapath/ansible` repo. For changes to cluster configuration logic, work in that repo and re-run `make ansible-setup` here to test.
