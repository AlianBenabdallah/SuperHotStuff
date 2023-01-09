use std::cmp::min;
use std::collections::HashSet;
use std::net::SocketAddr;

use crate::Parameters;
use crypto::PublicKey;

use crate::topologies::error::TopologyError;
use crate::topologies::traits::{Topology, TopologyBuilder};
use crate::topologies::types::{
    BinomialTreeTopology, BinomialTreeTopologyBuilder, FullMeshTopology, FullMeshTopologyBuilder,
    KauriTopology, KauriTopologyBuilder,
};

use super::types::CacheTopology;

impl TopologyBuilder for FullMeshTopologyBuilder {
    type Topology = FullMeshTopology;

    fn set_params(&mut self, _params: &Parameters, name: PublicKey) {
        self.name = Some(name);
    }

    fn build(
        &self,
        peers: Vec<(PublicKey, SocketAddr)>,
    ) -> Result<FullMeshTopology, TopologyError> {
        let name = self.name.ok_or(TopologyError::MissingParameters {
            param: "name".to_string(),
        })?;
        if peers.is_empty() {
            return Err(TopologyError::NoPeers);
        }
        let peers = peers.into_iter().filter(|(p, _)| p != &name).collect();
        Ok(FullMeshTopology { peers, name })
    }
}

impl Topology for FullMeshTopology {
    fn broadcast_peers(&mut self, name: PublicKey) -> Vec<(PublicKey, SocketAddr)> {
        if name == self.name {
            self.peers.clone()
        } else {
            vec![]
        }
    }

    fn indirect_peers(&mut self) -> Vec<(PublicKey, SocketAddr, usize)> {
        vec![]
    }
}

impl TopologyBuilder for KauriTopologyBuilder {
    type Topology = KauriTopology;

    fn set_params(&mut self, params: &Parameters, name: PublicKey) {
        self.fanout = params.fanout;
        self.name = Some(name)
    }

    // Builds an n-ary tree and add the children of id to peers
    fn build(&self, peers: Vec<(PublicKey, SocketAddr)>) -> Result<KauriTopology, TopologyError> {
        if peers.is_empty() {
            return Err(TopologyError::NoPeers);
        }

        let fanout = self
            .fanout
            .ok_or_else(|| TopologyError::MissingParameters {
                param: "fanout".to_string(),
            })?;
        let name = self.name.ok_or_else(|| TopologyError::MissingParameters {
            param: "name".to_string(),
        })?;
        Ok(KauriTopology::new(peers, fanout, name))
    }
}

impl Topology for KauriTopology {
    fn broadcast_peers(&mut self, id: PublicKey) -> Vec<(PublicKey, SocketAddr)> {
        // Find the index of the peer in the list
        let index = self
            .peers
            .iter()
            .position(|(peer_id, _)| peer_id == &id)
            .unwrap();

        // Place the sender at the beginning of the list
        self.peers.rotate_left(index);

        let mut processes_on_level = 1;
        let mut res = Vec::new();
        let mut i = 0;

        'building: loop {
            let mut start = i + processes_on_level;
            let remaining = self.peers.len() - start;
            if remaining == 0 {
                break 'building;
            }
            let max_fanout = remaining / processes_on_level;
            let curr_fanout = min(self.fanout, max_fanout);

            for _ in 0..processes_on_level {
                if i >= self.peers.len() || start >= self.peers.len() {
                    break 'building;
                }

                if self.name == self.peers[i].0 {
                    (start..min(start + curr_fanout, self.peers.len())).for_each(|j| {
                        res.push(self.peers[j]);
                    });
                }
                start += curr_fanout;
                i += 1;
            }
            processes_on_level = min(curr_fanout * processes_on_level, remaining);
        }

        // Place the sender at the end of the list
        self.peers.rotate_right(index);

        res
    }

    fn indirect_peers(&mut self) -> Vec<(PublicKey, SocketAddr, usize)> {
        // Returns the difference of self.peers and self.broadcast_peers(self.name)
        // Find the index of the peer in the list
        let index = self
            .peers
            .iter()
            .position(|(peer_id, _)| peer_id == &self.name)
            .unwrap();

        // Place the sender at the beginning of the list
        self.peers.rotate_left(index);

        let mut processes_on_level = min(self.fanout, self.peers.len() - 1);
        let mut res = Vec::new();
        let mut i = 1;
        let mut hop = 1;

        'building: loop {
            let mut start = i + processes_on_level;
            let remaining = self.peers.len() - start;
            if remaining == 0 {
                break 'building;
            }
            let max_fanout = remaining / processes_on_level;
            let curr_fanout = std::cmp::min(self.fanout, max_fanout);

            for _ in 0..processes_on_level {
                if i >= self.peers.len() || start >= self.peers.len() {
                    break 'building;
                }
                (start..min(start + curr_fanout, self.peers.len())).for_each(|j| {
                    res.push((self.peers[j].0, self.peers[j].1, hop));
                });
                start += curr_fanout;
                i += 1;
            }
            processes_on_level = min(curr_fanout * processes_on_level, remaining);
            hop += 1
        }

        // Place the sender at the end of the list
        self.peers.rotate_right(index);

        res
    }
}

impl TopologyBuilder for BinomialTreeTopologyBuilder {
    type Topology = BinomialTreeTopology;

    fn set_params(&mut self, _params: &Parameters, name: PublicKey) {
        self.name = Some(name)
    }

    fn build(
        &self,
        peers: Vec<(PublicKey, SocketAddr)>,
    ) -> Result<BinomialTreeTopology, TopologyError> {
        if peers.is_empty() {
            return Err(TopologyError::NoPeers);
        }

        let name = self.name.ok_or_else(|| TopologyError::MissingParameters {
            param: "name".to_string(),
        })?;
        Ok(BinomialTreeTopology::new(peers, name))
    }
}

impl Topology for BinomialTreeTopology {
    fn broadcast_peers(&mut self, sender: PublicKey) -> Vec<(PublicKey, SocketAddr)> {
        // Find the index of the peer in the list
        let index = self
            .peers
            .iter()
            .position(|(peer_id, _)| peer_id == &sender)
            .unwrap();

        // Place the sender at the beginning of the list
        self.peers.rotate_left(index);

        let mut res = Vec::new();
        let mut base = 1;
        if sender == self.name {
            // If the sender is the current node, then the result is self.peers[2^i] for i in [0, log2(peers.len())]
            while base < self.peers.len() {
                base <<= 1;
            }
            base >>= 1;
            while base > 0 {
                res.push(self.peers[base]);
                base >>= 1;
            }
        } else {
            let mut tmp =
                (self.my_index as i32 - index as i32).rem_euclid(self.peers.len() as i32) as usize;
            let fixed_index = tmp;
            while tmp != 0 && tmp % 2 == 0 {
                tmp >>= 1;
                base <<= 1;
            }
            base >>= 1;
            while base > 0 {
                let child_index = fixed_index + base;
                if child_index < self.peers.len() {
                    res.push(self.peers[child_index]);
                }
                base >>= 1;
            }
        }
        // Place the sender at the end of the list
        self.peers.rotate_right(index);
        res
    }

    fn indirect_peers(&mut self) -> Vec<(PublicKey, SocketAddr, usize)> {
        self.peers.rotate_left(self.my_index);
        let children: HashSet<_> = self.broadcast_peers(self.name).into_iter().collect();
        let mut res_set = HashSet::new();
        let mut res = Vec::new();
        let mut bitmask = 1;
        while bitmask < self.peers.len() {
            bitmask <<= 1;
        }
        bitmask >>= 1;
        let mut subchildren = vec![bitmask];
        let mut hop = 1;
        while bitmask > 0 {
            bitmask >>= 1;
            hop += 1;
            for i in 0..subchildren.len() {
                let v = subchildren[i] | bitmask;
                subchildren.push(v);
                if v < self.peers.len()
                    && !children.contains(&self.peers[v])
                    && res_set.insert(self.peers[v])
                    && self.peers[v].0 != self.name
                {
                    res.push((self.peers[v].0, self.peers[v].1, hop));
                }
            }
        }

        self.peers.rotate_right(self.my_index);

        res
    }
}

impl<T> Topology for CacheTopology<T>
where
    T: Topology,
{
    fn broadcast_peers(&mut self, id: PublicKey) -> Vec<(PublicKey, SocketAddr)> {
        if let Some(peers) = self.direct_peers_cache.get(&id) {
            peers.clone()
        } else {
            let peers = self.inner.broadcast_peers(id);
            self.direct_peers_cache.insert(id, peers.clone());
            peers
        }
    }

    fn indirect_peers(&mut self) -> Vec<(PublicKey, SocketAddr, usize)> {
        if let Some(peers) = &self.indirect_peers_cache {
            peers.clone()
        } else {
            let peers = self.inner.indirect_peers();
            self.indirect_peers_cache = Some(peers.clone());
            peers
        }
    }
}
