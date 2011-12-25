#!/usr/bin/perl -w

die "usage: rmbadlines inpt outpt dict\n" unless ($#ARGV==2); 

$infile = $ARGV[0];
$outfile = $ARGV[1];
$dict = $ARGV[2];

open DICT, $dict or die "unable to open dict\n";
%hash = ();

while (<DICT>) {
    s/[\n\r]//og;
    s/\t.*//og;
	$hash{lc($_)} = 1;
}
close(DICT);

open FIN, $infile or die "unable to open input\n";
open FOUT, ">", $outfile or die "unable to open output\n";

#print keys(%hash);

while (<FIN>) {
	$break = 0;
	$line = $_;
	s/[,;.]//og;
    s/\r\n//og;
	@words = split;
	foreach $w (@words) {
		if (not exists $hash{lc($w)} ) {
			print "*", lc($w), "\n", ;
			$break = 1;
		}
	}
	if ($break==0){
		print FOUT $line;
	}
}
close(FIN);
close(FOUT);



# 
# 
# %showtime4 = ();
# while (<FIN>) {
#     s/[\r\n]//og;
#     @fields = split;
#     die "bad format in db\n$_" unless ($#fields == 5);
#     $key = "$fields[0]\@$fields[1]";
#     $fields[2] =~ s/\.sph$//o;
#     $showtime = "$fields[2] $fields[4] $fields[5]";
#     $showtime4{$key} = $showtime;
# }
# close(FIN);
# 
# open(FIN, "<$dcdfile") or die "unable to open $dcdfile";
# while (<FIN>) {
#     s/[\r\n]//og;
#     next unless (/\@\d{4}\.dc:/o or /^=>/o);
#     if (/\@\d{4}\.dc:/o) {
#         ($key) = /^(\S+)\.dc:/o;
#         die "no showtime for $key" unless (defined($showtime4{$key}));
#         $showtime = $showtime4{$key};
#         @fields = split(/ /, $showtime);
#         $st = $fields[1];
#         $et = $fields[2];
#         $duration = $et-$st;
#         ($show, $speaker) = $key =~ /([^\#]+)\#(.+)/o;      
# 	die $_ unless defined $show;
#         die "bad showtime format $key\n" 
#             unless (defined($show) and defined($speaker));
#         $speaker =~ s/\@\d+$//o;
#     } else {
#         s/^=>\s+//o;
#         s/~SIL//og;
#         s/\s+/ /og;
#         s/^\s+//o;
#         s/\s+$//o;
#         @words = split;
#         $nwords = $#words + 1;
#         $interval = $duration / $nwords;
#         $t = $st;
#         foreach $w (@words) {
#             #$lex = ($w eq "<s>" or $w eq "</s>")?("non-lex"):("lex");
#             #$sp = ($lex eq "non-lex")?("null"):($speaker);
#             #print "$show\t1\t$t\t$interval\t$w\t0.8\t$lex\t$sp\n";
# 	    $w =~ tr/A-Z/a-z/;
#             print "$show\tA\t$t\t$interval\t$w\n" unless $w =~ m/<.?s>/;
#             $t += $interval;
#         }
#     }
# }
#         
