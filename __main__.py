
import os
import text_analyzer
import argparse
import utils

def validate_args(args):
    if args.event_id != 17972 and args.parse_crm_sql:
        raise argparse.ArgumentTypeError(f'The combination of event id filter {args.event_id} and Parse CRM SQL = True is not allowed. When using event id {args.event_id} remember to set --parse_crm_sql False')

    if not os.path.exists(args.event_dir):
        raise ValueError(f'The path to the eventX files {args.event_dir} does not exist')

    if args.similarity_threshold <= 0:
        raise argparse.ArgumentTypeError(f'The value for --similarity_threshold has to be in the interval of (0, 1]. - {args.similarity_threshold} <= 0')

    if args.similarity_threshold > 1.0:
        raise argparse.ArgumentTypeError(f'The value for --similarity_threshold has to be in the interval of (0, 1]. - {args.similarity_threshold} > 1.0')
    
def main(args):
    validate_args(args)
    text_analyzer.analyze(args.event_dir, args.event_id, args.parse_crm_sql, temp_dir=os.path.join(os.getcwd(), 'temp'), sim_threshold=args.similarity_threshold)    
    print('Process finished')
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='EventX Similarity Parser')
    parser.add_argument('-id', '--event_id', type=int, default=17972, help='Event Id that should be used to filter events. Examples: 1309 for .Net Events | \n 17972 (default) for CRM SQL Queries')
    parser.add_argument('-p', '--event_dir', help='Path to the event log dir. Default: /events', default=os.path.join(os.getcwd(), 'events'))
    parser.add_argument('-s', '--similarity_threshold', type=float, default=0.95, help='Similarity threshold used to compare event messages. Range (0.0 - 1.0] default: 0.95')
    parser.add_argument('-sql', '--parse_crm_sql', type=bool, default=True, help='Should CRM SQL event errors be parsed? - Can only be true (default) if event id is 17972.')
    args = parser.parse_args()
    main(args)




