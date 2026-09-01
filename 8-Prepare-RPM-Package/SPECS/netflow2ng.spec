%global debug_package %{nil}

Name:           netflow2ng
Version:        0.2.2
Release:        1%{?dist}
Summary:        NetFlow v9 collector for ntopng

License:        MIT
URL:            https://github.com/synfinatic/netflow2ng
Source0:        https://github.com/synfinatic/netflow2ng/archive/refs/tags/v%{version}.tar.gz

BuildRequires:  zeromq-devel, git

%description
netflow2ngi NetFlow v9 paketlerini ZeroMQ mesajlarıyla mesajlarıyla donusturup ntopng adli bir ag trafigi izleme aracina ileten koprudur.

%prep
%setup -q

%build
make

%install
mkdir -p %{buildroot}%{_bindir}
install -p -m 755 dist/%{name}-%{version} %{buildroot}%{_bindir}/%{name}

%files
%license LICENSE
%doc README.md
%{_bindir}/netflow2ng
