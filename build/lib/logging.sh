#!/bin/bash
log_to() { mkdir -p "$LOGOS_BUILD/logs"; exec > >(tee -a "$LOGOS_BUILD/logs/$1.log") 2>&1; }
