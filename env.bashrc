[ -f /etc/bash.bashrc ] && source /etc/bash.bashrc
[ -f $HOME/.bashrc ] && source $HOME/.bashrc
myenv=$(basename $(dirname $(realpath $0)))
PS1="($myenv) $PS1"
