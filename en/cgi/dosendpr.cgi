#!/usr/bin/perl
#
#  Send-pr perl script to send a pr.
#
# Copyright (c) 1996 Free Range Media
#
#  Copying and distribution permitted under the conditions of the
#  GNU General Public License Version 2.  
#     (http://www.gnu.ai.mit.edu/copyleft/gpl.html)
#
# $FreeBSD: www/en/cgi/dosendpr.cgi,v 1.8 2002/05/20 07:14:41 dd Exp $

require "html.pl";

use Socket;

my $blackhole = "relays.osirusoft.com";
my $openproxyip = "127.0.0.9";
my $blackhole_err = 0;
my $openproxy;

# isopenproxy ($ip, $blackhole_zone, $positive_ip)
# Returns undef on error, 0 if DNS lookup fails, $positive_ip if verified
# proxy. A DNS lookup failing can either means that there was a network
# problem, or that the IP is not listed in the blackhole zone.
sub isopenproxy ($$$) {
	# If $? is already set, then a successful gethostbyname() leaves it set
	local $?;
	my ($ip, $zone, $proxyip) = @_;
	my ($reversed_ip, $packed);
	if (!defined $proxyip) { return undef };

	$reversed_ip = join('.', reverse split(/\./, $ip));
	$packed = gethostbyname("${reversed_ip}.${blackhole}");
	return undef if $?;

	if ($packed && (inet_ntoa($packed) eq $proxyip)) {
		return $proxyip;
	} else {
		return 0;
	}
}

sub prerror {
    &html_title ("Problem Report Error");
    &html_body();
    print "There is an error in the configuration of the problem\n",
          "report form genator.  Please back up one page and report\n",
          "the problem to the owner of that page.  Report @_[0].";
    &html_end();
    exit (1);
}

&www_content ("text","html");
&cgi_form_in();

$gndb = $cgi_data{'gndb'};
if ($gndb =~ /^[a-z]+$/ && -e "$gndb.def")
  { require "$gndb.def"; }
else
  { &prerror("gndb problem"); }

&prerror("request method problem") if $ENV{'REQUEST_METHOD'} eq 'GET';

# Configuration
if ($gnhow eq "mail")
  {
    if (-e "/usr/lib/sendmail")
      { $submitprog = "/usr/lib/sendmail -t" };
    if (-e "/usr/sbin/sendmail")
      { $submitprog = "/usr/sbin/sendmail -t" };
  }
else
  { if (-e "$gnroot/queue-pr")
      { $submitprog = "$gnroot/queue-pr -q" };
  }

if (!$submitprog) { &prerror("submit program problem"); }

&html_title ($gnspreptitle);
&html_body ($gnsprepbody);

# Verify the data ...
if (!$cgi_data{'email'} || !$cgi_data{'originator'} ||
    !$cgi_data{'synopsis'}) {
    if ($gnsprepbad && -e $gnsprepbad )
      { print `cat $gnsprepbad`; }
    else {
	print "<h1>Bad Data</h1>\nYou need to specify at least your ",
          "electronic mail address, your name and a synopsis of the ",
          "of the problem.\n  Please return to the form and add the ",
          "missing information.  Thank you.\n";
    }
    &html_end();

    exit(1);
}

$openproxy = isopenproxy($ENV{'REMOTE_ADDR'}, $blackhole, $openproxyip);
if (defined $openproxy) {
	if ($openproxy) {
		&prerror("$ENV{'REMOTE_ADDR'} is an open proxy server");
	}
} else {
	$blackhole_err++;
}

# Build the PR.
$pr = "To: $gnemail\n" .
      "From: $cgi_data{'originator'} <$cgi_data{'email'}>\n" . 
      "Subject: $cgi_data{'synopsis'}\n" .
      "X-Originating-IP: $ENV{'REMOTE_ADDR'}\n";
if ($blackhole_err) {
      $pr .= "X-Originating-IP-Is-Open-Proxy: Maybe\n";
}
$pr .= "X-Send-Pr-Version: www-1.0\n\n" .
      ">Submitter-Id:\t$cgi_data{'submitterid'}\n" .
      ">Originator:\t$cgi_data{'originator'}\n" .
      ">Organization:\t$cgi_data{'organization'}\n" .
      ">Confidential:\t$cgi_data{'confidential'}\n" .
      ">Synopsis:\t$cgi_data{'synopsis'}\n" .
      ">Severity:\t$cgi_data{'severity'}\n" .
      ">Priority:\t$cgi_data{'priority'}\n" .
      ">Category:\t$cgi_data{'category'}\n" .
      ">Class:\t\t$cgi_data{'class'}\n" .
      ">Release:\t$cgi_data{'release'}\n" .
      ">Environment:\t$cgi_data{'environment'}\n" .
      ">Description:\n$cgi_data{'description'}\n" .
      ">How-To-Repeat:\n$cgi_data{'howtorepeat'}\n" .
      ">Fix:\n$cgi_data{'fix'}\n";

# remove any carrage returns that appear in the report.
$pr =~ s/\r//g;

#print "<PRE>$submitprog\n\n$pr\n</PRE>";
if (open (SUBMIT, "|$submitprog")){

    print SUBMIT $pr;
    close (SUBMIT);
    if ($gnspreppage && -e $gnspreppage )
      { print `cat $gnspreppage`; }
    else
      { print "<h1>Thank You</h1>",
	  "Thank you for the problem report.  You should receive confirmation",
	  " of your report by electronic mail within a day."; }
} else {
    print "<h1>Error</h1>An error occured processing your problem report.";
}
&html_end();
