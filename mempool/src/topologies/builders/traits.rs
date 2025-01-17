use crate::{topologies::traits::Topology, Parameters};

use crypto::PublicKey;
use std::net::SocketAddr;

use crate::topologies::builders::error::TopologyError;

/// `TopologyBuilder` is a trait that allows to build a topology.
pub trait TopologyBuilder: Clone {
    type Topology: Topology;

    /// 'new' initializes a TopologyBuilder with default parameters.
    fn new() -> Self;

    /// 'set_params' sets the parameters of the topology.
    fn set_params(&mut self, params: &Parameters, pub_key: PublicKey);

    /// `build` builds a topology from a list of peers.
    fn build(&self, peers: Vec<(PublicKey, SocketAddr)>) -> Result<Self::Topology, TopologyError>;
}
